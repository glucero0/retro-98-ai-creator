"""Gmail read-only access for the search_gmail Gemini tool."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from .config import expand_path, load_config

logger = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_TOKEN_REL = ".retro-98-ai-creator/gmail_token.json"
DEFAULT_MAX_RESULTS = 20
MAX_RESULTS_CAP = 50
MAX_BODY_BYTES = 32 * 1024  # per message when include_body is true


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


def _gmail_section(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    section = cfg.get("gmail")
    return dict(section or {})


def _token_path(cfg: dict[str, Any] | None = None) -> Path:
    section = _gmail_section(cfg)
    rel = (section.get("token_path") or DEFAULT_TOKEN_REL).strip() or DEFAULT_TOKEN_REL
    return expand_path(rel)


def _credentials_path(cfg: dict[str, Any] | None = None) -> Path | None:
    section = _gmail_section(cfg)
    raw = (section.get("credentials_path") or "").strip()
    if not raw:
        return None
    return expand_path(raw)


def _load_stored_credentials(token_path: Path) -> Any | None:
    if not token_path.is_file():
        return None
    try:
        from google.oauth2.credentials import Credentials

        return Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    except Exception as exc:  # noqa: BLE001
        logger.info("Could not load Gmail token: %s", exc)
        return None


def _save_credentials(creds: Any, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")


def _refresh_credentials(creds: Any) -> Any:
    from google.auth.transport.requests import Request

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_gmail_credentials(cfg: dict[str, Any] | None = None) -> Any | None:
    """Return valid Gmail credentials, refreshing the token file when needed."""
    cfg = cfg or load_config()
    token_path = _token_path(cfg)
    creds = _load_stored_credentials(token_path)
    if not creds:
        return None
    if not creds.valid:
        creds = _refresh_credentials(creds)
        if creds and creds.valid:
            _save_credentials(creds, token_path)
    return creds if creds and creds.valid else None


def gmail_auth_status(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Report whether Gmail OAuth is configured and authorized."""
    cfg = cfg or load_config()
    creds_path = _credentials_path(cfg)
    token_path = _token_path(cfg)
    creds = get_gmail_credentials(cfg)
    return {
        "ok": True,
        "configured": creds_path is not None and creds_path.is_file(),
        "authorized": creds is not None,
        "credentials_path": str(creds_path) if creds_path else "",
        "token_path": str(token_path),
    }


def authorize_gmail(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Run the desktop OAuth flow (opens the system browser).

    Requires credentials_path in config pointing to a Google OAuth client JSON file.
    """
    cfg = cfg or load_config()
    creds_path = _credentials_path(cfg)
    if creds_path is None:
        return {
            "ok": False,
            "error": (
                "Gmail OAuth client JSON path is not set. Pick credentials in "
                "Control Panel → Gmail, then Save."
            ),
        }
    if not creds_path.is_file():
        return {
            "ok": False,
            "error": f"Gmail credentials file not found: {creds_path}",
        }

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return {
            "ok": False,
            "error": (
                "google-auth-oauthlib is not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib"
            ),
        }

    token_path = _token_path(cfg)
    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), GMAIL_SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
        _save_credentials(creds, token_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gmail authorization failed: %s", exc)
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "authorized": True,
        "token_path": str(token_path),
        "message": "Gmail authorized successfully.",
    }


def _build_gmail_service(cfg: dict[str, Any] | None = None) -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "google-api-python-client is not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib"
        ) from exc

    creds = get_gmail_credentials(cfg)
    if creds is None:
        raise RuntimeError(
            "Gmail is not authorized. Open Control Panel → Gmail and click "
            "Connect Gmail after saving your OAuth client JSON path."
        )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


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
