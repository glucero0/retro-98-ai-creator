"""Tests for the browse_web tool."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

from synthetic_text_extruder.web_browse import (
    _html_to_text_and_links,
    _normalize_http_url,
    browse_web,
)


def test_normalize_adds_https_and_rejects_file():
    assert _normalize_http_url("example.com/path") == "https://example.com/path"
    try:
        _normalize_http_url("file:///C:/secret.txt")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "http" in str(exc).lower()


def test_browse_web_requires_url():
    result = browse_web("")
    assert result["ok"] is False
    assert "url" in result["error"].lower()


def test_html_extracts_title_text_and_links():
    html = """
    <html><head><title>Docs Home</title>
    <script>secret()</script></head>
    <body>
      <h1>Welcome</h1>
      <p>Read the <a href="/guide">guide</a> or
      <a href="https://other.test/a">elsewhere</a>.</p>
      <a href="javascript:alert(1)">nope</a>
    </body></html>
    """
    title, text, links = _html_to_text_and_links(html, "https://docs.test/index")
    assert title == "Docs Home"
    assert "Welcome" in text
    assert "secret()" not in text
    hrefs = [item["url"] for item in links]
    assert "https://docs.test/guide" in hrefs
    assert "https://other.test/a" in hrefs
    assert all(not h.startswith("javascript:") for h in hrefs)


def test_browse_web_fetches_html_page():
    html = (
        b"<html><head><title>Example</title></head>"
        b"<body><p>Hello site</p><a href='/next'>Next</a></body></html>"
    )
    resp = MagicMock()
    resp.geturl.return_value = "https://example.com/"
    resp.status = 200
    resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    resp.read.return_value = html
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False

    with patch("synthetic_text_extruder.web_browse.urlopen", return_value=resp):
        result = browse_web("https://example.com/")

    assert result["ok"] is True
    assert result["title"] == "Example"
    assert "Hello site" in result["text"]
    assert result["links"][0]["url"] == "https://example.com/next"
    assert result["links"][0]["text"] == "Next"


def test_browse_web_can_omit_links():
    resp = MagicMock()
    resp.geturl.return_value = "https://example.com/plain"
    resp.status = 200
    resp.headers = {"Content-Type": "text/plain"}
    resp.read.return_value = b"just text"
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False

    with patch("synthetic_text_extruder.web_browse.urlopen", return_value=resp):
        result = browse_web("https://example.com/plain", include_links=False)

    assert result["ok"] is True
    assert result["text"] == "just text"
    assert "links" not in result


def test_browse_web_reports_http_error():
    from urllib.error import HTTPError

    err = HTTPError("https://example.com/missing", 404, "Not Found", hdrs=None, fp=BytesIO())
    with patch("synthetic_text_extruder.web_browse.urlopen", side_effect=err):
        result = browse_web("https://example.com/missing")
    assert result["ok"] is False
    assert "404" in result["error"]
