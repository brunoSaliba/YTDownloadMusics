# System — YT Music Downloader

- Single service `web`: FastAPI (`app/main.py`), Uvicorn `--workers 1`, static page in `app/static/` (no build, no inline JS).
- `POST /api/info {url}` → `validation.extract_video_id` (host allowlist + `^[A-Za-z0-9_-]{11}$`) → child `python -m app.worker info <id>`.
- `GET /api/download/{id}` → child `python -m app.worker download <id> <tmpdir>`; yt-dlp re-checks duration/live via `match_filter` before downloading, converts to MP3 192k with tags + cover; the MP3 (≤ ~22 MB by the duration cap) is read into memory and the temp dir deleted before responding; `sweep_stale_workdirs` deletes leftovers > 10 min.
- Child processes (`app/jobs.py`): fixed argv, no shell, own process group, killed on timeout (info 45 s, download 240 s). Worker prints one JSON line; error codes map to HTTP in `main.ERRORS` (400/422/502/503/504).
- Concurrency: non-blocking semaphores, 2 info / 2 downloads per process (limits memory under the 768m cap) → 503.
- yt-dlp hardening: only the canonical URL rebuilt from the ID, `allowed_extractors=["youtube"]`, `noplaylist`, `cachedir=False`, `max_filesize`, `YTDLP_NO_PLUGINS=1`; optional `FORCE_IPV6=1` binds yt-dlp to IPv6 (`source_address="::"`); optional YouTube cookies (Compose secret `/run/secrets/youtube_cookies`) are filtered (Netscape, youtube.com/google.com only) into a per-job 0600 copy in tmpfs, deleted after the job, values redacted from stderr; Deno runs via yt-dlp-ejs with no permissions.
- No DB, no persistent storage, no runtime secrets. Config via env (see `deploy/.env.example`).
