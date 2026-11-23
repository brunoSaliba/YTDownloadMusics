"""FastAPI app: static page + /api/info + /api/download/{id}."""

import logging
import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import jobs
from app.config import load_settings
from app.validation import extract_video_id, is_valid_video_id, safe_download_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("app")

STATIC_DIR = Path(__file__).resolve().parent / "static"
settings = load_settings()
info_slots = jobs.Slots(settings.max_concurrent_info)
download_slots = jobs.Slots(settings.max_concurrent_jobs)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' https://i.ytimg.com; script-src 'self'; "
        "style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
        "form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}

# worker error code -> (HTTP status, user message)
ERRORS = {
    "invalid": (400, "URL inválida. Cole um link de vídeo do YouTube."),
    "too_long": (422, f"Vídeo muito longo. O limite é {settings.max_duration_seconds // 60} minutos."),
    "live": (422, "Transmissões ao vivo não são suportadas."),
    "no_duration": (422, "Não foi possível determinar a duração do vídeo."),
    "playlist": (422, "Playlists não são suportadas. Cole o link de um único vídeo."),
    "unavailable": (422, "Vídeo indisponível, privado ou com restrição."),
    "too_large": (422, "Arquivo muito grande ou falha na conversão."),
    "blocked": (502, "O YouTube bloqueou a requisição. Tente novamente mais tarde."),
    "failed": (502, "Não foi possível processar o vídeo. Tente novamente."),
    "timeout": (504, "O processamento demorou demais. Tente novamente."),
    "busy": (503, "Servidor ocupado. Tente novamente em instantes."),
}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    logger.exception("unhandled error on %s", request.url.path)
    # Runs outside the http middleware, so headers are set explicitly here.
    return JSONResponse({"detail": "Erro interno."}, status_code=500, headers=SECURITY_HEADERS)


def _fail(code: str) -> HTTPException:
    status, message = ERRORS.get(code, ERRORS["failed"])
    return HTTPException(status_code=status, detail=message)


class InfoRequest(BaseModel):
    url: str = Field(max_length=2048)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return PlainTextResponse("User-agent: *\nDisallow: /api/\n")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/info")
def info(body: InfoRequest):
    video_id = extract_video_id(body.url)
    if not video_id:
        raise _fail("invalid")
    if not info_slots.acquire():
        raise _fail("busy")
    try:
        result = jobs.run_worker(["info", video_id], timeout=settings.info_timeout_seconds)
    finally:
        info_slots.release()
    logger.info("info id=%s ok=%s error=%s", video_id, result.ok, result.error)
    if not result.ok:
        raise _fail(result.error or "failed")
    return result.info


@app.get("/api/download/{video_id}")
def download(video_id: str):
    if not is_valid_video_id(video_id):
        raise _fail("invalid")
    if not download_slots.acquire():
        raise _fail("busy")
    workdir = None
    try:
        jobs.sweep_stale_workdirs()
        workdir = jobs.new_workdir()
        result = jobs.run_worker(["download", video_id, workdir], timeout=settings.job_timeout_seconds)
        logger.info("download id=%s ok=%s error=%s", video_id, result.ok, result.error)
        path = os.path.join(workdir, f"{video_id}.mp3")
        if not result.ok:
            raise _fail(result.error or "failed")
        if not os.path.isfile(path):
            raise _fail("failed")
        info = result.info or {}
        filename = safe_download_name(str(info.get("artist") or ""), str(info.get("title") or video_id))
        # Size is bounded by MAX_DURATION_SECONDS (~22 MB for 15 min @ 192k). Reading into memory
        # lets the temp dir be deleted before responding, so no client behaviour can leak it.
        content = Path(path).read_bytes()
    finally:
        # The slot bounds conversion work only; sending the finished file needs no slot.
        if workdir:
            jobs.remove_workdir(workdir)
        download_slots.release()
    return Response(
        content=content,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{quote(filename)}"},
    )
