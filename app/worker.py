"""Child-process entry point: `python -m app.worker info|download <video_id> [workdir]`.

Runs yt-dlp/ffmpeg/Deno outside the web process so the parent can kill the
whole process group on timeout. Receives only a validated video ID (never a
user URL) and prints exactly one JSON line to stdout.
"""

import json
import os
import sys

# Defense in depth (also set in the Dockerfile): never load yt-dlp plugins.
os.environ["YTDLP_NO_PLUGINS"] = "1"

from yt_dlp import YoutubeDL  # noqa: E402
from yt_dlp.utils import DownloadError  # noqa: E402

from app.config import Settings, load_settings
from app.validation import canonical_url, is_valid_video_id, thumbnail_url


class JobError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class _StderrLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        print(msg, file=sys.stderr)

    def error(self, msg):
        print(msg, file=sys.stderr)


def base_opts(settings: Settings) -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "allowed_extractors": ["youtube"],
        "cachedir": False,
        "socket_timeout": 15,
        "retries": 2,
        "extractor_retries": 1,
        "fragment_retries": 2,
        "max_filesize": settings.max_filesize_mb * 1024 * 1024,
        "logger": _StderrLogger(),
    }


def check_info(info: dict, settings: Settings) -> None:
    """Reject playlists, live streams and over-long videos (invariant I4)."""
    if info.get("_type") in ("playlist", "multi_video"):
        raise JobError("playlist")
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming", "post_live"):
        raise JobError("live")
    duration = info.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise JobError("no_duration")
    if duration > settings.max_duration_seconds:
        raise JobError("too_long")


def public_info(info: dict, video_id: str) -> dict:
    artists = info.get("artists")
    artist = ", ".join(a for a in artists if isinstance(a, str)) if isinstance(artists, list) else ""
    artist = artist or info.get("artist") or info.get("uploader") or info.get("channel") or ""
    title = info.get("track") or info.get("title") or video_id
    return {
        "id": video_id,
        "title": str(title)[:300],
        "artist": str(artist)[:200],
        "duration": int(info.get("duration") or 0),
        "thumbnail": thumbnail_url(video_id),
    }


def classify_error(exc: Exception) -> str:
    msg = str(exc).lower()
    unavailable = ("unavailable", "private video", "removed", "not available", "members-only", "confirm your age")
    if "not a bot" in msg:
        return "blocked"
    if any(s in msg for s in unavailable):
        return "unavailable"
    return "failed"


def _ensure_same_video(info: dict, video_id: str) -> None:
    if info.get("id") != video_id:
        raise JobError("unavailable")


def run_info(video_id: str, settings: Settings, ydl_cls=YoutubeDL) -> dict:
    with ydl_cls(base_opts(settings) | {"format": "bestaudio/best"}) as ydl:
        info = ydl.extract_info(canonical_url(video_id), download=False)
    _ensure_same_video(info, video_id)
    check_info(info, settings)
    return public_info(info, video_id)


def run_download(video_id: str, workdir: str, settings: Settings, ydl_cls=YoutubeDL) -> dict:
    """Download + convert to MP3, re-validating limits before any media download."""
    rejected: list[JobError] = []

    def match_filter(info, incomplete=False):
        if incomplete:
            return None
        try:
            _ensure_same_video(info, video_id)
            check_info(info, settings)
        except JobError as exc:
            rejected.append(exc)
            return exc.code
        return None

    opts = base_opts(settings) | {
        "format": "bestaudio/best",
        "paths": {"home": workdir, "temp": workdir},
        "outtmpl": {"default": "%(id)s.%(ext)s"},
        "overwrites": True,
        "writethumbnail": True,
        "match_filter": match_filter,
        "postprocessors": [
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
    }
    with ydl_cls(opts) as ydl:
        info = ydl.extract_info(canonical_url(video_id), download=True)
    if rejected:
        raise rejected[0]
    if not os.path.isfile(os.path.join(workdir, f"{video_id}.mp3")):
        raise JobError("too_large")
    return public_info(info, video_id)


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def main(argv: list[str]) -> int:
    if len(argv) < 2 or not is_valid_video_id(argv[1]):
        _emit({"ok": False, "error": "invalid"})
        return 2
    mode, video_id = argv[0], argv[1]
    settings = load_settings()
    try:
        if mode == "info" and len(argv) == 2:
            result = run_info(video_id, settings)
        elif mode == "download" and len(argv) == 3 and os.path.isdir(argv[2]):
            result = run_download(video_id, argv[2], settings)
        else:
            _emit({"ok": False, "error": "invalid"})
            return 2
    except JobError as exc:
        _emit({"ok": False, "error": exc.code})
        return 1
    except DownloadError as exc:
        print(str(exc)[:500], file=sys.stderr)
        _emit({"ok": False, "error": classify_error(exc)})
        return 1
    except Exception as exc:  # noqa: BLE001 - child must always answer with JSON
        print(f"{type(exc).__name__}: {str(exc)[:500]}", file=sys.stderr)
        _emit({"ok": False, "error": "failed"})
        return 1
    _emit({"ok": True, "info": result})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
