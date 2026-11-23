"""Trust-boundary validation: user URLs become a validated video ID or nothing.

Invariant I1: only the canonical URL rebuilt from a validated ID is ever handed
to yt-dlp; the user-supplied URL is never forwarded.
"""

import re
import unicodedata
from urllib.parse import parse_qs, urlsplit

VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
MAX_URL_LENGTH = 2048

_WATCH_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_SHORT_HOSTS = {"youtu.be", "www.youtu.be"}
_FORBIDDEN_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
MAX_FILENAME_LENGTH = 150


def is_valid_video_id(value: object) -> bool:
    return isinstance(value, str) and VIDEO_ID_RE.fullmatch(value) is not None


def extract_video_id(url: object) -> str | None:
    """Return the 11-char video ID for an allowed YouTube URL, else None."""
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url or len(url) > MAX_URL_LENGTH:
        return None
    if "://" not in url:
        url = "https://" + url
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    if parts.username or parts.password or port not in (None, 80, 443):
        return None

    host = (parts.hostname or "").lower()
    segments = [s for s in parts.path.split("/") if s]
    candidate = None
    if host in _SHORT_HOSTS:
        if len(segments) == 1:
            candidate = segments[0]
    elif host in _WATCH_HOSTS:
        if segments == ["watch"]:
            values = parse_qs(parts.query).get("v")
            if values and len(values) == 1:
                candidate = values[0]
        elif len(segments) == 2 and segments[0] == "shorts":
            candidate = segments[1]
    return candidate if is_valid_video_id(candidate) else None


def canonical_url(video_id: str) -> str:
    if not is_valid_video_id(video_id):
        raise ValueError("invalid video id")
    return f"https://www.youtube.com/watch?v={video_id}"


def thumbnail_url(video_id: str) -> str:
    if not is_valid_video_id(video_id):
        raise ValueError("invalid video id")
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def safe_download_name(artist: str, title: str) -> str:
    """Build a header-safe `Artist - Title.mp3` (invariant I3)."""
    base = f"{artist} - {title}" if artist else title
    base = unicodedata.normalize("NFC", base or "")
    base = "".join(" " if unicodedata.category(ch).startswith("C") else ch for ch in base)
    base = _FORBIDDEN_FILENAME_CHARS.sub(" ", base)
    base = re.sub(r"\s+", " ", base).strip(" .")
    base = base[:MAX_FILENAME_LENGTH].rstrip(" .")
    return (base or "audio") + ".mp3"
