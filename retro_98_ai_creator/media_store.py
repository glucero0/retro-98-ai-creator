"""File-backed storage for generated images and videos."""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, load_config

_SAFE_ID = re.compile(r"[^a-zA-Z0-9_-]+")

EXT_FOR_MIME: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}

MIME_FOR_EXT: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


def media_dir(config: dict[str, Any] | None = None) -> Path:
    cfg = config if config is not None else load_config()
    rel = ((cfg.get("paths") or {}).get("media") or "media").strip() or "media"
    path = Path(rel).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_stem(creation_id: str) -> str:
    stem = _SAFE_ID.sub("_", (creation_id or "media").strip()) or "media"
    return stem[:80]


def extension_for_mime(mime_type: str | None, fallback: str = ".bin") -> str:
    mime = (mime_type or "").strip().lower()
    if mime in EXT_FOR_MIME:
        return EXT_FOR_MIME[mime]
    guessed = mimetypes.guess_extension(mime.split(";")[0].strip()) if mime else None
    return guessed or fallback


def mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME_FOR_EXT:
        return MIME_FOR_EXT[ext]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def write_media_bytes(
    creation_id: str,
    data: bytes,
    *,
    mime_type: str,
    config: dict[str, Any] | None = None,
    suffix: str | None = None,
) -> dict[str, str]:
    """Write bytes under media/ and return relative mediaPath + mimeType."""
    if not data:
        raise ValueError("Empty media payload")
    ext = suffix or extension_for_mime(mime_type)
    if not ext.startswith("."):
        ext = "." + ext
    filename = f"{_safe_stem(creation_id)}{ext}"
    dest = media_dir(config) / filename
    dest.write_bytes(data)
    # Store path relative to project root for portability
    try:
        rel = dest.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        rel = dest.resolve().as_posix()
    return {"mediaPath": rel, "mimeType": mime_type or mime_for_path(dest)}


def resolve_media_path(media_path: str | None, config: dict[str, Any] | None = None) -> Path | None:
    if not media_path:
        return None
    p = Path(str(media_path).strip())
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    p = p.resolve()
    if not p.exists() or not p.is_file():
        return None
    # Soft safety: prefer files under project or configured media dir
    return p


def read_media_bytes(media_path: str | None, config: dict[str, Any] | None = None) -> bytes | None:
    path = resolve_media_path(media_path, config)
    if path is None:
        return None
    return path.read_bytes()


def media_data_url(media_path: str | None, mime_type: str | None = None) -> str | None:
    raw = read_media_bytes(media_path)
    if raw is None:
        return None
    path = resolve_media_path(media_path)
    mime = (mime_type or (mime_for_path(path) if path else None) or "application/octet-stream")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def media_file_uri(media_path: str | None) -> str | None:
    path = resolve_media_path(media_path)
    if path is None:
        return None
    return path.as_uri()
