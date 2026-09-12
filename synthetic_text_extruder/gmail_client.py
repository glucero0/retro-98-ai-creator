"""Gmail search for the search_gmail Gemini tool."""

from __future__ import annotations

import base64
import logging
from typing import Any

from .google_auth import (
    GMAIL_READONLY,
    authorize_gmail,
    build_google_service,
    get_gmail_credentials,
    gmail_auth_status,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 20
MAX_RESULTS_CAP = 50
MAX_BODY_BYTES = 32 * 1024  # per message when include_body is true

__all__ = [
    "authorize_gmail",
    "get_gmail_credentials",
    "gmail_auth_status",
    "search_gmail",
]


def _decode_base64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _truncate_text(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    trimmed = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return trimmed + "\n…[body truncated]"


def _build_gmail_service(cfg: dict[str, Any] | None = None) -> Any:
    return build_google_service(
        "gmail",
        "v1",
        cfg,
        required_scopes=[GMAIL_READONLY],
    )


def _header_value(headers: list[dict[str, str]] | None, name: str) -> str:
    target = name.lower()
    for item in headers or []:
        if (item.get("name") or "").lower() == target:
            return str(item.get("value") or "")
    return ""


def _extract_plain_body(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""

    mime_type = (payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")
    if mime_type == "text/plain" and data:
        return _decode_base64url(str(data))

    parts = payload.get("parts") or []
    for part in parts:
        part_mime = (part.get("mimeType") or "").lower()
        part_body = part.get("body") or {}
        part_data = part_body.get("data")
        if part_mime == "text/plain" and part_data:
            return _decode_base64url(str(part_data))

    for part in parts:
        nested = _extract_plain_body(part)
        if nested:
            return nested

    for part in parts:
        part_mime = (part.get("mimeType") or "").lower()
        part_body = part.get("body") or {}
        part_data = part_body.get("data")
        if part_mime == "text/html" and part_data:
            return _decode_base64url(str(part_data))

    return ""


def _normalize_max_results(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_RESULTS
    if n < 1:
        n = 1
    return min(n, MAX_RESULTS_CAP)


def _message_summary(
    service: Any,
    msg_id: str,
    *,
    include_body: bool,
) -> dict[str, Any]:
    if include_body:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        headers = detail.get("payload", {}).get("headers") or []
        body = _truncate_text(
            _extract_plain_body(detail.get("payload")),
            MAX_BODY_BYTES,
        )
        snippet = str(detail.get("snippet") or "")
    else:
        detail = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )
        headers = detail.get("payload", {}).get("headers") or []
        body = ""
        snippet = str(detail.get("snippet") or "")

    labels = list(detail.get("labelIds") or [])
    return {
        "id": msg_id,
        "thread_id": str(detail.get("threadId") or ""),
        "from": _header_value(headers, "From"),
        "to": _header_value(headers, "To"),
        "subject": _header_value(headers, "Subject"),
        "date": _header_value(headers, "Date"),
        "snippet": snippet,
        "labels": labels,
        "is_unread": "UNREAD" in labels,
        "body": body if include_body else None,
    }


def search_gmail(
    query: str,
    *,
    max_results: int | None = None,
    include_body: bool = False,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Search the user's Gmail inbox using Gmail search syntax.

    Returns a JSON-serializable dict suitable for Gemini tool responses.
    """
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "query is required (Gmail search syntax)"}

    limit = _normalize_max_results(
        max_results if max_results is not None else DEFAULT_MAX_RESULTS
    )
    want_body = bool(include_body)

    try:
        service = _build_gmail_service(cfg)
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        listed = (
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=limit)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("Gmail list failed for query %r: %s", q, exc)
        return {"ok": False, "error": f"Gmail API error: {exc}", "query": q}

    raw_messages = listed.get("messages") or []
    messages: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in raw_messages:
        msg_id = str(item.get("id") or "")
        if not msg_id:
            continue
        try:
            messages.append(
                _message_summary(service, msg_id, include_body=want_body)
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{msg_id}: {exc}")

    result_size_estimate = listed.get("resultSizeEstimate")
    try:
        estimate = int(result_size_estimate) if result_size_estimate is not None else None
    except (TypeError, ValueError):
        estimate = None

    out: dict[str, Any] = {
        "ok": True,
        "query": q,
        "max_results": limit,
        "include_body": want_body,
        "count": len(messages),
        "result_size_estimate": estimate,
        "messages": messages,
    }
    if errors:
        out["partial_errors"] = errors
    return out
