import pytest

from app.validation import canonical_url, extract_video_id, safe_download_name

VID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"youtube.com/watch?v={VID}&list=PL123&t=42s",
        f"https://m.youtube.com/watch?v={VID}",
        f"https://music.youtube.com/watch?v={VID}&si=abc",
        f"https://youtu.be/{VID}?si=xyz",
        f"https://www.youtube.com/shorts/{VID}",
        f"  http://YOUTUBE.com/watch?v={VID}  ",
    ],
)
def test_accepts_supported_youtube_urls(url):
    assert extract_video_id(url) == VID


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://169.254.169.254/latest/meta-data",
        f"https://youtube.com.evil.com/watch?v={VID}",
        f"https://evil.com/?u=https://youtube.com/watch?v={VID}",
        f"https://user:pw@youtube.com/watch?v={VID}",
        f"https://youtube.com:8080/watch?v={VID}",
        f"file:///etc/passwd?v={VID}",
        "https://www.youtube.com/watch?v=../../etc/pa",
        "https://www.youtube.com/playlist?list=PL1234567890",
        f"https://www.youtube.com/watch?v={VID}&v=aaaaaaaaaaa",
        "https://youtu.be/short",
        "https://www.youtube.com/watch?v=" + "a" * 3000,
    ],
)
def test_rejects_non_youtube_or_malformed_urls(url):
    """I1: anything outside the allowlist never yields an ID for yt-dlp."""
    assert extract_video_id(url) is None


def test_canonical_url_is_rebuilt_from_id_only():
    assert canonical_url(VID) == f"https://www.youtube.com/watch?v={VID}"
    with pytest.raises(ValueError):
        canonical_url("../../etc/x")


def test_download_name_is_header_and_path_safe():
    """I3: no CR/LF, quotes, separators or control chars reach Content-Disposition."""
    name = safe_download_name('Evil/Band\\', 'Song"\r\nSet-Cookie: x=1\x00<script>')
    assert name.endswith(".mp3")
    for bad in ("\r", "\n", '"', "/", "\\", "\x00", "<", ">"):
        assert bad not in name
    assert len(name) <= 154
    assert safe_download_name("", "") == "audio.mp3"
    assert safe_download_name("A" * 400, "B") == "A" * 150 + ".mp3"
