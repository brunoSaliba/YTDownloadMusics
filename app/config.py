"""Runtime configuration read from environment variables."""

import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    max_duration_seconds: int
    max_concurrent_jobs: int
    max_concurrent_info: int
    job_timeout_seconds: int
    info_timeout_seconds: int
    max_filesize_mb: int
    force_ipv6: bool = False
    cookies_file: str = "/run/secrets/youtube_cookies"


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def load_settings() -> Settings:
    return Settings(
        max_duration_seconds=_positive_int("MAX_DURATION_SECONDS", 900),
        max_concurrent_jobs=_positive_int("MAX_CONCURRENT_JOBS", 2),
        max_concurrent_info=_positive_int("MAX_CONCURRENT_INFO", 2),
        job_timeout_seconds=_positive_int("JOB_TIMEOUT_SECONDS", 240),
        info_timeout_seconds=_positive_int("INFO_TIMEOUT_SECONDS", 45),
        max_filesize_mb=_positive_int("MAX_FILESIZE_MB", 100),
        force_ipv6=_flag("FORCE_IPV6"),
        cookies_file=os.environ.get("YOUTUBE_COOKIES_FILE", "/run/secrets/youtube_cookies"),
    )
