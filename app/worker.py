"""Child-process entry point: `python -m app.worker info|download <video_id> [workdir]`.

Runs yt-dlp/ffmpeg/Deno outside the web process so the parent can kill the
whole process group on timeout. Receives only a validated video ID (never a
user URL) and prints exactly one JSON line to stdout.
"""

import contextlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile

# Defense in depth (also set in the Dockerfile): never load yt-dlp plugins.
os.environ["YTDLP_NO_PLUGINS"] = "1"

from yt_dlp import YoutubeDL  # noqa: E402
from yt_dlp.utils import DownloadError  # noqa: E402

from app.config import Settings, load_settings
from app.jobs import WORKDIR_PREFIX
from app.validation import canonical_url, is_valid_video_id, thumbnail_url


class JobError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


COOKIE_MAX_BYTES = 1024 * 1024
COOKIE_DOMAINS = ("youtube.com", "google.com")
COOKIE_HEADER = "# Netscape HTTP Cookie File\n"

# Cookie values of the current job, redacted from anything written to stderr (C2).
_SECRETS: list[str] = []


def _redact(msg: object) -> str:
    text = str(msg)
    for secret in _SECRETS:
        text = text.replace(secret, "***")
    return text


# Any control char but TAB (e.g. a stray CR) would split the line again inside
# yt-dlp, which then echoes the fragments raw to stderr (C2).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")


class _RedactingStream:
    """stderr wrapper: yt-dlp's write_string() bypasses the logger (C2)."""

    def __init__(self, stream):
        self._stream = stream
        self.encoding = getattr(stream, "encoding", "utf-8")

    def write(self, text):
        return self._stream.write(_redact(text))

    def flush(self):
        self._stream.flush()

    def isatty(self):
        return False


class _StderrLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        print(_redact(msg), file=sys.stderr)

    def error(self, msg):
        print(_redact(msg), file=sys.stderr)


def _read_cookie_source(path: str) -> str | None:
    """Read the operator cookie file once: regular file, no symlink, <= 1 MiB (C5)."""
    if not path:
        return None
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        data = b""
        while len(data) <= COOKIE_MAX_BYTES:
            chunk = os.read(fd, COOKIE_MAX_BYTES + 1 - len(data))
            if not chunk:
                break
            data += chunk
    except OSError:
        return None
    finally:
        os.close(fd)
    if not data or len(data) > COOKIE_MAX_BYTES:
        return None
    return data.decode("utf-8", errors="replace")


def _valid_cookie_line(line: str) -> bool:
    if _CONTROL_CHARS.search(line):
        return False
    fields = line.split("\t")
    if len(fields) != 7:
        return False
    raw_domain = fields[0].removeprefix("#HttpOnly_")
    domain = raw_domain.lstrip(".").lower()
    if not any(domain == d or domain.endswith("." + d) for d in COOKIE_DOMAINS):
        return False
    # MozillaCookieJar rejects the whole file unless the flag matches the leading dot.
    if fields[1] != ("TRUE" if raw_domain.startswith(".") else "FALSE"):
        return False
    expires = fields[4]
    return fields[3] in ("TRUE", "FALSE") and expires.isascii() and expires.isdigit() and fields[5] != ""


def filter_cookie_lines(text: str) -> list[str]:
    """Keep only well-formed Netscape lines for YouTube/Google (C1, C2)."""
    lines = (raw.rstrip("\r") for raw in text.split("\n"))
    return [line for line in lines if _valid_cookie_line(line)]


@contextlib.contextmanager
def cookie_copy(settings: Settings):
    """Yield a private, filtered, per-job copy of the cookie file, or None (C3, C4)."""
    text = _read_cookie_source(settings.cookies_file)
    lines = filter_cookie_lines(text) if text else []
    if not lines:
        yield None
        return
    values = (line.split("\t")[6] for line in lines)
    _SECRETS.extend(v for v in values if len(v) >= 8)
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix=WORKDIR_PREFIX)
        path = os.path.join(tmpdir, "cookies.txt")
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(COOKIE_HEADER + "\n".join(lines) + "\n")
    except OSError:
        path = None  # cannot stage cookies: run without them (C4)
    try:
        yield path
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def base_opts(settings: Settings, cookiefile: str | None = None) -> dict:
    opts = {
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
    if settings.force_ipv6:
        # YouTube may block a host's IPv4 ("not a bot"); bind to IPv6 only.
        opts["source_address"] = "::"
    if cookiefile:
        opts["cookiefile"] = cookiefile
    return opts


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


def run_info(video_id: str, settings: Settings, ydl_cls=None) -> dict:
    opts = {"format": "bestaudio/best"}
    ydl_cls = ydl_cls or YoutubeDL
    with cookie_copy(settings) as cookiefile, ydl_cls(base_opts(settings, cookiefile) | opts) as ydl:
        info = ydl.extract_info(canonical_url(video_id), download=False)
    _ensure_same_video(info, video_id)
    check_info(info, settings)
    return public_info(info, video_id)


def run_download(video_id: str, workdir: str, settings: Settings, ydl_cls=None) -> dict:
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

    opts = {
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
    ydl_cls = ydl_cls or YoutubeDL
    with cookie_copy(settings) as cookiefile, ydl_cls(base_opts(settings, cookiefile) | opts) as ydl:
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
    sys.stderr = _RedactingStream(sys.stderr)
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
        print(_redact(exc)[:500], file=sys.stderr)
        _emit({"ok": False, "error": classify_error(exc)})
        return 1
    except Exception as exc:  # noqa: BLE001 - child must always answer with JSON
        print(f"{type(exc).__name__}: {_redact(exc)[:500]}", file=sys.stderr)
        _emit({"ok": False, "error": "failed"})
        return 1
    _emit({"ok": True, "info": result})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
