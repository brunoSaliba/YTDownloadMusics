import os
import sys
import time

import pytest
from fastapi.testclient import TestClient

from app import jobs, main
from app.jobs import WorkerResult

VID = "dQw4w9WgXcQ"
INFO = {"id": VID, "title": 'Song "x"', "artist": "Band", "duration": 200,
        "thumbnail": f"https://i.ytimg.com/vi/{VID}/hqdefault.jpg"}


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def workdirs(monkeypatch, tmp_path):
    created = []

    def new_workdir():
        path = tmp_path / f"w{len(created)}"
        path.mkdir()
        created.append(path)
        return str(path)

    monkeypatch.setattr(jobs, "new_workdir", new_workdir)
    return created


def fake_worker(result, write_mp3=False, calls=None):
    def run(args, timeout):
        if calls is not None:
            calls.append(args)
        if write_mp3:
            with open(os.path.join(args[2], f"{args[1]}.mp3"), "wb") as fh:
                fh.write(b"ID3fake")
        return result
    return run


def test_index_health_robots_and_security_headers(client):
    page = client.get("/")
    assert page.status_code == 200 and 'id="url"' in page.text
    assert "<script>" not in page.text  # no inline JS (CSP)
    csp = page.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in csp and "img-src 'self' https://i.ytimg.com" in csp
    assert page.headers["x-content-type-options"] == "nosniff"
    assert client.get("/healthz").json() == {"status": "ok"}
    assert "Disallow: /api/" in client.get("/robots.txt").text


def test_info_returns_metadata(client, monkeypatch):
    calls = []
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), calls=calls))
    res = client.post("/api/info", json={"url": f"https://youtu.be/{VID}?list=PL1"})
    assert res.status_code == 200 and res.json() == INFO
    assert calls == [["info", VID]]


def test_info_rejects_bad_url_without_spawning_worker(client, monkeypatch):
    calls = []
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), calls=calls))
    res = client.post("/api/info", json={"url": "http://169.254.169.254/?v=dQw4w9WgXcQ"})
    assert res.status_code == 400 and calls == []


def test_download_rejects_malformed_id(client, monkeypatch):
    calls = []
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), calls=calls))
    assert client.get("/api/download/..%2F..%2Fetc%2Fpasswd").status_code in (400, 404)
    assert client.get("/api/download/abc").status_code == 400
    assert calls == []


@pytest.mark.parametrize(("error", "status"), [("too_long", 422), ("live", 422), ("blocked", 502), ("timeout", 504)])
def test_download_maps_worker_errors_and_cleans_temp(client, monkeypatch, workdirs, error, status):
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(False, error=error)))
    res = client.get(f"/api/download/{VID}")
    assert res.status_code == status
    assert "detail" in res.json()
    assert not workdirs[0].exists()


def test_download_serves_mp3_and_removes_temp(client, monkeypatch, workdirs):
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), write_mp3=True))
    res = client.get(f"/api/download/{VID}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    disposition = res.headers["content-disposition"]
    assert disposition.startswith("attachment;") and "Band%20-%20Song%20x.mp3" in disposition
    assert res.content == b"ID3fake"
    assert not workdirs[0].exists()


def test_download_range_request_does_not_leak_temp(client, monkeypatch, workdirs):
    """I4: an unsatisfiable Range header cannot leave the work dir on disk."""
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), write_mp3=True))
    client.get(f"/api/download/{VID}", headers={"Range": "bytes=999999999-"})
    assert not workdirs[0].exists()


def test_download_busy_returns_503(client, monkeypatch, workdirs):
    monkeypatch.setattr(main, "download_slots", jobs.Slots(1))
    assert main.download_slots.acquire()
    calls = []
    monkeypatch.setattr(jobs, "run_worker", fake_worker(WorkerResult(True, info=INFO), calls=calls))
    res = client.get(f"/api/download/{VID}")
    assert res.status_code == 503 and calls == []


def test_run_worker_kills_hung_child_on_timeout(monkeypatch):
    """I4: a hung job is killed and reported as timeout instead of holding a slot."""
    monkeypatch.setattr(jobs, "worker_command", lambda *a: [sys.executable, "-c", "import time; time.sleep(30)"])
    start = time.monotonic()
    result = jobs.run_worker(["download", VID, "x"], timeout=1)
    assert result == WorkerResult(ok=False, error="timeout")
    assert time.monotonic() - start < 10


def test_run_worker_parses_child_json(monkeypatch):
    script = 'import json; print("noise"); print(json.dumps({"ok": True, "info": {"id": "x"}}))'
    monkeypatch.setattr(jobs, "worker_command", lambda *a: [sys.executable, "-c", script])
    assert jobs.run_worker(["info", VID], timeout=20) == WorkerResult(ok=True, info={"id": "x"})
