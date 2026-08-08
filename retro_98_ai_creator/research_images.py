"""Discover and OCR images referenced during search research."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .extract_text import MAX_INLINE_BYTES, ocr_image_bytes

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

MAX_SEARCH_IMAGES = 5
MIN_IMAGE_BYTES = 2048
FETCH_TIMEOUT_SEC = 15
MAX_PAGE_FETCHES = 3

_IMAGE_EXT_RE = re.compile(r"\.(?:png|jpe?g|webp|gif)(?:\?|#|$)", re.IGNORECASE)
_URL_IN_TEXT_RE = re.compile(r"""https?://[^\s<>"')\]]+""", re.IGNORECASE)
_IMG_SRC_RE = re.compile(
    r"""<img[^>]+src=["']([^"']+)["']""",
    re.IGNORECASE,
)
_OG_IMAGE_RE = re.compile(
    r"""<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']""",
    re.IGNORECASE,
)
_OG_IMAGE_RE_ALT = re.compile(
    r"""<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']""",
    re.IGNORECASE,
)

_USER_AGENT = "Retro98AICreator/0.1 (research image OCR)"


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:  # noqa: BLE001
        return ""


def domain_allowed(url: str, allowed_domains: set[str]) -> bool:
    """True when the URL host matches a cited grounding domain."""
    host = _domain(url)
    if not host or not allowed_domains:
        return False
    for allowed in allowed_domains:
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def allowed_domains_from_sources(sources: list[dict[str, str]] | None) -> set[str]:
    domains: set[str] = set()
    for src in sources or []:
        url = (src.get("url") or "").strip()
        domain = _domain(url)
        if domain:
            domains.add(domain)
    return domains


def _looks_like_image_url(url: str) -> bool:
    raw = (url or "").strip()
    if not raw.lower().startswith(("http://", "https://")):
        return False
    path = urlparse(raw).path.lower()
    return bool(_IMAGE_EXT_RE.search(path))


def _normalize_url(url: str, base_url: str = "") -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if raw.startswith("//"):
        raw = "https:" + raw
    if base_url and not raw.lower().startswith(("http://", "https://")):
        raw = urljoin(base_url, raw)
    return raw


def extract_image_urls_from_text(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in _URL_IN_TEXT_RE.finditer(text or ""):
        url = match.group(0).rstrip(".,;)")
        if not _looks_like_image_url(url):
            continue
        key = url.lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(url)
    return found


def extract_image_urls_from_html(html: str, *, base_url: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    patterns = (_IMG_SRC_RE, _OG_IMAGE_RE, _OG_IMAGE_RE_ALT)
    for pattern in patterns:
        for match in pattern.finditer(html or ""):
            url = _normalize_url(match.group(1), base_url)
            if not url or not _looks_like_image_url(url):
                continue
            key = url.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(url)
    return found


def discover_image_urls(
    research_context: str,
    *,
    grounding_sources: list[dict[str, str]] | None,
    max_page_fetches: int = MAX_PAGE_FETCHES,
) -> list[str]:
    """Collect candidate image URLs from research text and cited pages."""
    allowed = allowed_domains_from_sources(grounding_sources)
    if not allowed:
        return []

    ordered: list[str] = []
    seen: set[str] = set()

    def add(url: str) -> None:
        normalized = _normalize_url(url)
        if not normalized or not _looks_like_image_url(normalized):
            return
        if not domain_allowed(normalized, allowed):
            return
        key = normalized.lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(normalized)

    for url in extract_image_urls_from_text(research_context):
        add(url)

    page_urls: list[str] = []
    for src in grounding_sources or []:
        page = (src.get("url") or "").strip()
        if page and not _looks_like_image_url(page):
            page_urls.append(page)

    fetched = 0
    for page_url in page_urls:
        if fetched >= max_page_fetches:
            break
        try:
            html = _fetch_text(page_url, max_bytes=512 * 1024)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not fetch page for image discovery %s: %s", page_url, exc)
            continue
        fetched += 1
        for img_url in extract_image_urls_from_html(html, base_url=page_url):
            add(img_url)

    return ordered


def _fetch_text(url: str, *, max_bytes: int) -> str:
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=FETCH_TIMEOUT_SEC) as resp:  # noqa: S310
        data = resp.read(max_bytes + 1)
    if len(data) > max_bytes:
        data = data[:max_bytes]
    charset = "utf-8"
    return data.decode(charset, errors="replace")


def _guess_mime(url: str, content_type: str | None) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct.startswith("image/"):
        return ct
    path = urlparse(url).path.lower()
    if path.endswith(".png"):
        return "image/png"
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        return "image/jpeg"
    if path.endswith(".webp"):
        return "image/webp"
    if path.endswith(".gif"):
        return "image/gif"
    return "image/png"


def download_image(url: str, *, max_bytes: int = MAX_INLINE_BYTES) -> tuple[bytes, str] | None:
    """Download image bytes when safe; returns (data, mime_type) or None."""
    try:
        req = Request(url, headers={"User-Agent": _USER_AGENT})
        with urlopen(req, timeout=FETCH_TIMEOUT_SEC) as resp:  # noqa: S310
            content_type = resp.headers.get("Content-Type")
            data = resp.read(max_bytes + 1)
        if len(data) < MIN_IMAGE_BYTES:
            return None
        if len(data) > max_bytes:
            logger.debug("Skipping oversized search image %s (%d bytes)", url, len(data))
            return None
        mime = _guess_mime(url, content_type)
        if not mime.startswith("image/"):
            return None
        return data, mime
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not download search image %s: %s", url, exc)
        return None


def _emit_progress(
    progress: ProgressCallback | None,
    message: str,
    *,
    percent: float | None = None,
) -> None:
    if not progress:
        return
    from .cancellation import GenerationCancelled

    payload: dict[str, Any] = {
        "message": message,
        "phase": "generate",
        "title": "Searching",
    }
    if percent is not None:
        payload["percent"] = percent
    try:
        progress(payload)
    except GenerationCancelled:
        raise
    except Exception:  # noqa: BLE001
        logger.debug("progress callback failed", exc_info=True)


def enrich_research_with_image_ocr(
    research_context: str,
    *,
    grounding_sources: list[dict[str, str]] | None,
    config: dict[str, Any],
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
) -> tuple[str, dict[str, Any]]:
    """
    Download and OCR images referenced in research findings.

    Returns (append_block, meta). append_block is empty when nothing useful was found.
    """
    from .cancellation import raise_if_cancelled

    def _cancelled() -> bool:
        return bool(cancel_event is not None and cancel_event.is_set())

    raise_if_cancelled(_cancelled)

    candidates = discover_image_urls(
        research_context,
        grounding_sources=grounding_sources,
    )
    meta: dict[str, Any] = {
        "ocrImageCount": 0,
        "ocrImageUrls": [],
        "ocr_search_images": False,
    }
    if not candidates:
        return "", meta

    _emit_progress(progress, "OCR on search images…", percent=32)

    findings: list[str] = []
    processed = 0
    for url in candidates:
        if processed >= MAX_SEARCH_IMAGES:
            break
        raise_if_cancelled(_cancelled)

        downloaded = download_image(url)
        if not downloaded:
            continue
        raw, mime_type = downloaded

        try:
            text, _model = ocr_image_bytes(
                raw,
                mime_type=mime_type,
                config=config,
                progress=progress,
                cancel_event=cancel_event,
            )
        except Exception as exc:  # noqa: BLE001
            from .cancellation import GenerationCancelled

            if isinstance(exc, GenerationCancelled):
                raise
            logger.warning("OCR failed for search image %s: %s", url, exc)
            continue

        cleaned = (text or "").strip()
        if not cleaned or cleaned == "(no text found)":
            continue

        processed += 1
        meta["ocrImageUrls"].append(url)
        findings.append(f"- {url}\n  {cleaned}")

    if not findings:
        return "", meta

    meta["ocrImageCount"] = processed
    meta["ocr_search_images"] = True
    block = (
        "IMAGE OCR FINDINGS (from search sources):\n"
        + "\n\n".join(findings)
        + "\n"
    )
    return block, meta
