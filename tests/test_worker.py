import json

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
)


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
