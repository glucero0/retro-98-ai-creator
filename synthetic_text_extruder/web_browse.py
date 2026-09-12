"""Fetch an http(s) page and return readable text plus links for browse_web."""

from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 24_000
MAX_CHARS_CAP = 48_000
MAX_DOWNLOAD_BYTES = 512 * 1024
MAX_LINKS = 40
FETCH_TIMEOUT_SEC = 20
_USER_AGENT = "Retro98AICreator/0.1 (browse_web)"
_SKIP_TAGS = frozenset({"script", "style", "noscript", "svg", "template"})
_BLOCK_HREF_PREFIXES = ("javascript:", "data:", "mailto:", "tel:", "#")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._parts: list[str] = []
        self._links: list[tuple[str, str]] = []
        self._title_parts: list[str] = []
        self._in_title = False
        self._in_anchor = False
        self._anchor_href = ""
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        if name in _SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return
        if name == "title":
            self._in_title = True
        if name in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "hr"}:
            self._parts.append("\n")
        if name == "a":
            href = ""
            for key, value in attrs:
                if key.lower() == "href" and value:
                    href = value.strip()
                    break
            self._in_anchor = True
            self._anchor_href = href
            self._anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in _SKIP_TAGS and self._skip:
            self._skip -= 1
            return
        if self._skip:
            return
        if name == "title":
            self._in_title = False
        if name == "a" and self._in_anchor:
            self._in_anchor = False
            text = " ".join("".join(self._anchor_text).split())
            if self._anchor_href:
                self._links.append((self._anchor_href, text))

    def handle_data(self, data: str) -> None:
        if self._skip or not data:
            return
        if self._in_title:
            self._title_parts.append(data)
            return
        if self._in_anchor:
            self._anchor_text.append(data)
        collapsed = " ".join(data.split())
        if collapsed:
            self._parts.append(collapsed + " ")

    def title(self) -> str:
        return " ".join("".join(self._title_parts).split())

    def text(self) -> str:
        raw = "".join(self._parts)
        return re.sub(r"\n{3,}", "\n\n", raw).strip()

    def links(self) -> list[tuple[str, str]]:
        return list(self._links)


def _normalize_http_url(raw: str) -> str:
    url = (raw or "").strip()
    if not url:
        raise ValueError("url is required")
    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        raise ValueError("url must be http or https")
    if not (parsed.netloc or "").strip():
        raise ValueError("url is missing a host")
    return url


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme or "").lower() in {"http", "https"} and bool(parsed.netloc)


def _normalize_max_chars(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_CHARS
    if n < 500:
        n = 500
    return min(n, MAX_CHARS_CAP)


def _html_to_text_and_links(html: str, base_url: str) -> tuple[str, str, list[dict[str, str]]]:
    parser = _PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001
        logger.debug("HTML parse failed for %s", base_url)
    title = parser.title()
    text = parser.text()
    seen: set[str] = set()
    links: list[dict[str, str]] = []
    for href, label in parser.links():
        if not href or href.lower().startswith(_BLOCK_HREF_PREFIXES):
            continue
        absolute = urljoin(base_url, href)
        if not _is_http_url(absolute):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append({"url": absolute, "text": label})
        if len(links) >= MAX_LINKS:
            break
    return title, text, links


def _fetch(url: str) -> tuple[str, int, str, str]:
    req = Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=FETCH_TIMEOUT_SEC) as resp:  # noqa: S310
            final_url = str(resp.geturl() or url)
            status = int(getattr(resp, "status", None) or 200)
            content_type = str(resp.headers.get("Content-Type") or "")
            data = resp.read(MAX_DOWNLOAD_BYTES + 1)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"could not fetch {url}: {exc.reason}") from exc

    if not _is_http_url(final_url):
        raise ValueError("redirected to a non-http URL")
    truncated_download = len(data) > MAX_DOWNLOAD_BYTES
    if truncated_download:
        data = data[:MAX_DOWNLOAD_BYTES]
    charset = "utf-8"
    ct_lower = content_type.lower()
    if "charset=" in ct_lower:
        charset = ct_lower.split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
    text = data.decode(charset, errors="replace")
    return final_url, status, content_type, text


def browse_web(
    url: str,
    *,
    include_links: bool = True,
    max_chars: int | None = None,
) -> dict[str, Any]:
    """
    Fetch an http(s) URL and return readable text (and optional outbound links).

    The model can construct query URLs and follow returned links on later calls.
    """
    try:
        requested = _normalize_http_url(url)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        final_url, status, content_type, raw = _fetch(requested)
    except Exception as exc:  # noqa: BLE001
        logger.info("browse_web failed for %r: %s", requested, exc)
        return {"ok": False, "error": str(exc), "requested_url": requested}

    ct = (content_type or "").split(";")[0].strip().lower()
    title = ""
    links: list[dict[str, str]] = []
    if "html" in ct or raw.lstrip()[:15].lower().startswith(("<!doctype html", "<html")):
        title, text, links = _html_to_text_and_links(raw, final_url)
    else:
        text = raw.strip()

    limit = _normalize_max_chars(max_chars if max_chars is not None else DEFAULT_MAX_CHARS)
    truncated = len(text) > limit
    if truncated:
        text = text[:limit] + "\n…[truncated]"

    out: dict[str, Any] = {
        "ok": True,
        "requested_url": requested,
        "url": final_url,
        "status": status,
        "content_type": content_type,
        "title": title,
        "text": text,
        "truncated": truncated,
        "chars": len(text),
    }
    if include_links:
        out["links"] = links
        out["link_count"] = len(links)
    return out
