"""Google Drive search and file create for Gemini tools."""

from __future__ import annotations

import logging
from typing import Any

from .google_auth import DRIVE_FILE, DRIVE_READONLY, build_google_service

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 20
MAX_RESULTS_CAP = 50
MAX_CONTENT_BYTES = 32 * 1024


def _normalize_max_results(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_RESULTS
    if n < 1:
        n = 1
    return min(n, MAX_RESULTS_CAP)


def search_drive(
    query: str,
    *,
    max_results: int | None = None,
    mime_type: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Search Drive files using Drive query syntax (name contains, mimeType, …)."""
    q = (query or "").strip()
    extra_mime = (mime_type or "").strip()
    if extra_mime:
        mime_clause = f"mimeType = '{extra_mime}'"
        q = f"({q}) and {mime_clause}" if q else mime_clause
    if not q:
        return {
            "ok": False,
            "error": "query is required (Drive search syntax, e.g. name contains 'report')",
        }

    limit = _normalize_max_results(
        max_results if max_results is not None else DEFAULT_MAX_RESULTS
    )
    try:
        service = build_google_service(
            "drive",
            "v3",
            cfg,
            required_scopes=[DRIVE_READONLY],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        listed = (
            service.files()
            .list(
                q=q,
                pageSize=limit,
                fields="files(id,name,mimeType,modifiedTime,webViewLink,parents,size)",
                spaces="drive",
            )
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("Drive list failed for query %r: %s", q, exc)
        return {"ok": False, "error": f"Drive API error: {exc}", "query": q}

    files = []
    for item in listed.get("files") or []:
        files.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "mime_type": str(item.get("mimeType") or ""),
                "modified": str(item.get("modifiedTime") or ""),
                "url": str(item.get("webViewLink") or ""),
                "parents": list(item.get("parents") or []),
                "size": item.get("size"),
            }
        )
    return {
        "ok": True,
        "query": q,
        "max_results": limit,
        "count": len(files),
        "files": files,
    }


def create_drive_file(
    name: str,
    *,
    content: str | None = None,
    mime_type: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a Drive file (text/plain by default) owned by this app."""
    title = (name or "").strip()
    if not title:
        return {"ok": False, "error": "name is required"}

    mime = (mime_type or "").strip() or "text/plain"
    text = content if content is not None else ""
    if not isinstance(text, str):
        text = str(text)
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_CONTENT_BYTES:
        return {
            "ok": False,
            "error": f"content too large ({len(encoded)} bytes); max is {MAX_CONTENT_BYTES}",
        }

    try:
        service = build_google_service(
            "drive",
            "v3",
            cfg,
            required_scopes=[DRIVE_FILE],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(encoded, mimetype=mime, resumable=False)
        created = (
            service.files()
            .create(
                body={"name": title, "mimeType": mime},
                media_body=media,
                fields="id,name,mimeType,webViewLink",
            )
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("Drive create failed for %r: %s", title, exc)
        return {"ok": False, "error": f"Drive API error: {exc}"}

    return {
        "ok": True,
        "id": str(created.get("id") or ""),
        "name": str(created.get("name") or title),
        "mime_type": str(created.get("mimeType") or mime),
        "url": str(created.get("webViewLink") or ""),
        "bytes_written": len(encoded),
    }
