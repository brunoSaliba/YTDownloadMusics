import json
import os

import pytest

from app import worker
from app.config import Settings

VID = "dQw4w9WgXcQ"
SETTINGS = Settings(
    max_duration_seconds=900,
    max_concurrent_jobs=2,
    max_concurrent_info=4,
    job_timeout_seconds=240,
    info_timeout_seconds=45,
    max_filesize_mb=100,
    cookies_file="",
)


@pytest.fixture(autouse=True)
def _no_leaked_secrets(monkeypatch):
    monkeypatch.setattr(worker, "_SECRETS", [])


def fake_ydl(info, calls):
    """Mimics YoutubeDL: applies match_filter before 'downloading'."""

    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts
            calls.append(("init", opts))

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False):
            calls.append(("extract", url, download))
            mf = self.opts.get("match_filter")
            if download and (mf is None or mf(info, incomplete=False) is None):
                calls.append(("downloaded",))
            return info

    return FakeYDL


def test_info_maps_metadata_and_builds_thumbnail_server_side():
    calls = []
    info = {"id": VID, "title": "Video", "track": "Song", "artists": ["A", "B"],
            "uploader": "Chan", "duration": 200, "thumbnail": "javascript:alert(1)"}
    result = worker.run_info(VID, SETTINGS, ydl_cls=fake_ydl(info, calls))
    assert result == {"id": VID, "title": "Song", "artist": "A, B", "duration": 200,
                      "thumbnail": f"https://i.ytimg.com/vi/{VID}/hqdefault.jpg"}
    assert calls[1] == ("extract", f"https://www.youtube.com/watch?v={VID}", False)
    assert calls[0][1]["allowed_extractors"] == ["youtube"]
    assert calls[0][1]["noplaylist"] is True


def test_artist_falls_back_to_uploader():
    info = {"id": VID, "title": "T", "uploader": "Chan", "duration": 10}
    assert worker.public_info(info, VID)["artist"] == "Chan"


@pytest.mark.parametrize(
    ("info", "code"),
    [
        ({"id": VID, "duration": 36000}, "too_long"),
        ({"id": VID, "duration": 100, "is_live": True}, "live"),
        ({"id": VID, "live_status": "is_upcoming", "duration": 100}, "live"),
        ({"id": VID}, "no_duration"),
        ({"id": "otherVideo1", "duration": 100}, "unavailable"),
    ],
)
def test_download_revalidates_limits_before_downloading(tmp_path, info, code):
    """I4: calling the download path directly cannot bypass duration/live checks."""
    calls = []
    with pytest.raises(worker.JobError) as exc:
        worker.run_download(VID, str(tmp_path), SETTINGS, ydl_cls=fake_ydl(info, calls))
    assert exc.value.code == code
    assert ("downloaded",) not in calls


def test_download_succeeds_when_mp3_exists(tmp_path):
    calls = []
    (tmp_path / f"{VID}.mp3").write_bytes(b"ID3")
    info = {"id": VID, "title": "T", "uploader": "U", "duration": 100}
    result = worker.run_download(VID, str(tmp_path), SETTINGS, ydl_cls=fake_ydl(info, calls))
    assert result["title"] == "T"
    opts = calls[0][1]
    assert opts["max_filesize"] == 100 * 1024 * 1024
    assert {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"} in opts["postprocessors"]


def test_main_rejects_invalid_id_without_running_ytdlp(capsys):
    assert worker.main(["info", "../../x"]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "error": "invalid"}


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ("Sign in to confirm you're not a bot", "blocked"),
        ("Video unavailable", "unavailable"),
        ("Sign in to confirm your age. This video may be inappropriate", "unavailable"),
        ("HTTP Error 500 with some message", "failed"),
    ],
)
def test_classify_error(message, code):
    assert worker.classify_error(Exception(message)) == code


def test_force_ipv6_binds_source_address_only_when_enabled():
    from dataclasses import replace

    assert "source_address" not in worker.base_opts(SETTINGS)
    assert worker.base_opts(replace(SETTINGS, force_ipv6=True))["source_address"] == "::"


# --- FEAT-002: YouTube cookies -------------------------------------------------
TAB = chr(9)
GOOD = TAB.join([".youtube.com", "TRUE", "/", "TRUE", "1999999999", "SID", "secret-sid-value-123"])
EVIL = TAB.join([".evil.com", "TRUE", "/", "TRUE", "1999999999", "X", "evil-value-123456"])
INFO_OK = {"id": VID, "title": "T", "duration": 10}


def _with_cookies(path):
    from dataclasses import replace

    return replace(SETTINGS, cookies_file=str(path))


def test_ytdlp_gets_private_filtered_cookie_copy_removed_after_job(tmp_path):
    """AC1/AC2, C1, C3: filtered 0600 copy is used, then deleted; original untouched."""
    import stat
    from pathlib import Path

    src = tmp_path / "cookies.txt"
    original = "# Netscape HTTP Cookie File\n" + GOOD + "\n" + EVIL + "\n"
    src.write_text(original)
    seen = {}

    class YDL(fake_ydl(INFO_OK, [])):
        def extract_info(self, url, download=False):
            path = self.opts["cookiefile"]
            seen.update(path=path, content=Path(path).read_text(),
                        mode=stat.S_IMODE(os.stat(path).st_mode))
            return super().extract_info(url, download)

        def __exit__(self, *exc):
            seen["exists_on_exit"] = os.path.exists(self.opts["cookiefile"])  # yt-dlp saves here
            return False

    worker.run_info(VID, _with_cookies(src), ydl_cls=YDL)
    assert seen["path"] != str(src)
    assert GOOD in seen["content"] and "evil" not in seen["content"]
    if os.name == "posix":
        assert seen["mode"] == 0o600
    assert seen["exists_on_exit"] is True
    assert not os.path.exists(os.path.dirname(seen["path"]))
    assert src.read_text() == original


def test_download_also_uses_cookies(tmp_path):
    """AC1: the download path gets the cookie copy too."""
    src = tmp_path / "cookies.txt"
    src.write_text(GOOD + "\n")
    calls = []
    with pytest.raises(worker.JobError):  # fake writes no mp3
        worker.run_download(VID, str(tmp_path), _with_cookies(src), ydl_cls=fake_ydl(INFO_OK, calls))
    assert "cookiefile" in calls[0][1]


@pytest.mark.parametrize("kind", ["missing", "empty", "directory", "too_big", "malformed", "flag_mismatch",
                                  "symlink"])
def test_unusable_cookie_file_runs_without_cookies(tmp_path, kind):
    """AC3, C4/C5: anything but a small regular file with valid lines -> no cookies."""
    path = tmp_path / "c.txt"
    if kind == "empty":
        path.write_text("")
    elif kind == "directory":
        path.mkdir()
    elif kind == "too_big":
        path.write_text(GOOD + "\n" + "#" * worker.COOKIE_MAX_BYTES)
    elif kind == "malformed":
        path.write_text(GOOD.replace(TAB, " ") + "\n")
    elif kind == "flag_mismatch":  # MozillaCookieJar would reject the whole file
        path.write_text(GOOD.replace("youtube.com" + TAB + "TRUE", "youtube.com" + TAB + "FALSE") + "\n")
    elif kind == "symlink":
        if os.name != "posix":
            pytest.skip("symlinks need POSIX")
        real = tmp_path / "real.txt"
        real.write_text(GOOD + "\n")
        path.symlink_to(real)
    calls = []
    worker.run_info(VID, _with_cookies(path), ydl_cls=fake_ydl(INFO_OK, calls))
    assert "cookiefile" not in calls[0][1]


def test_cookie_values_never_reach_stdout_or_stderr(tmp_path, monkeypatch, capsys):
    """AC4/AC5, C2: malformed lines never reach yt-dlp; errors are redacted and map to blocked."""
    from pathlib import Path

    from yt_dlp.utils import DownloadError

    bad_secret = "malformed-secret-777"
    cr_secret = "carriage-secret-888"
    src = tmp_path / "c.txt"
    cr_line = TAB.join([".youtube.com", "TRUE", "/", "TRUE", "0", "N\rX", cr_secret])
    src.write_bytes((GOOD + "\n" + " ".join([".youtube.com", "TRUE", "/", "TRUE", "0", "X", bad_secret])
                     + "\n" + cr_line + "\n").encode())
    monkeypatch.setenv("YOUTUBE_COOKIES_FILE", str(src))

    class Boom(fake_ydl(INFO_OK, [])):
        def extract_info(self, url, download=False):
            from yt_dlp.utils import write_string

            staged = Path(self.opts["cookiefile"]).read_bytes()
            assert bad_secret.encode() not in staged and cr_secret.encode() not in staged
            self.opts["logger"].error("cookie secret-sid-value-123 rejected")
            write_string("WARNING: raw secret-sid-value-123\n")  # bypasses the logger
            raise DownloadError("Sign in to confirm you're not a bot secret-sid-value-123")

    monkeypatch.setattr(worker, "YoutubeDL", Boom)
    assert worker.main(["info", VID]) == 1
    out, err = capsys.readouterr()
    assert json.loads(out) == {"ok": False, "error": "blocked"}
    for secret in ("secret-sid-value-123", bad_secret, cr_secret):
        assert secret not in out and secret not in err
