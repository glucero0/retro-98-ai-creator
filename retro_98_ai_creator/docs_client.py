"""Google Docs read / create / edit for Gemini tools."""

from __future__ import annotations

import logging
from typing import Any

from .google_auth import DOCUMENTS, DOCUMENTS_READONLY, build_google_service

logger = logging.getLogger(__name__)

MAX_DOC_CHARS = 48_000


def _extract_doc_text(document: dict[str, Any]) -> str:
    chunks: list[str] = []
    for element in (document.get("body") or {}).get("content") or []:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for part in paragraph.get("elements") or []:
            text_run = part.get("textRun") or {}
            content = text_run.get("content")
            if content:
                chunks.append(str(content))
    return "".join(chunks)


def _end_index(document: dict[str, Any]) -> int:
    content = (document.get("body") or {}).get("content") or []
    if not content:
        return 1
    try:
        return int(content[-1].get("endIndex") or 1)
    except (TypeError, ValueError):
        return 1


def _truncate(text: str) -> str:
    if len(text) <= MAX_DOC_CHARS:
        return text
    return text[:MAX_DOC_CHARS] + "\n…[document truncated]"


def read_google_doc(
    document_id: str,
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc_id = (document_id or "").strip()
    if not doc_id:
        return {"ok": False, "error": "document_id is required"}

    try:
        service = build_google_service(
            "docs",
            "v1",
            cfg,
            required_scopes=[DOCUMENTS_READONLY],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        document = service.documents().get(documentId=doc_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Docs get failed for %r: %s", doc_id, exc)
        return {"ok": False, "error": f"Docs API error: {exc}", "document_id": doc_id}

    text = _extract_doc_text(document)
    return {
        "ok": True,
        "document_id": doc_id,
        "title": str(document.get("title") or ""),
        "text": _truncate(text),
        "revision_id": str(document.get("revisionId") or ""),
    }


def create_google_doc(
    title: str,
    *,
    text: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = (title or "").strip()
    if not name:
        return {"ok": False, "error": "title is required"}

    try:
        service = build_google_service(
            "docs",
            "v1",
            cfg,
            required_scopes=[DOCUMENTS],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        created = service.documents().create(body={"title": name}).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Docs create failed for %r: %s", name, exc)
        return {"ok": False, "error": f"Docs API error: {exc}"}

    doc_id = str(created.get("documentId") or "")
    body = text if text is not None else ""
    if not isinstance(body, str):
        body = str(body)
    if body:
        edited = edit_google_doc(doc_id, text=body, mode="replace", cfg=cfg)
        if not edited.get("ok"):
            return {
                "ok": False,
                "document_id": doc_id,
                "title": str(created.get("title") or name),
                "error": edited.get("error") or "created the document but failed to insert text",
            }
        return edited

    return {
        "ok": True,
        "document_id": doc_id,
        "title": str(created.get("title") or name),
        "text": "",
        "url": f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else "",
    }


def edit_google_doc(
    document_id: str,
    *,
    text: str,
    mode: str = "replace",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc_id = (document_id or "").strip()
    if not doc_id:
        return {"ok": False, "error": "document_id is required"}
    if text is None:
        return {"ok": False, "error": "text is required"}
    if not isinstance(text, str):
        text = str(text)

    action = (mode or "replace").strip().lower()
    if action not in {"replace", "append"}:
        return {"ok": False, "error": "mode must be 'replace' or 'append'"}

    try:
        service = build_google_service(
            "docs",
            "v1",
            cfg,
            required_scopes=[DOCUMENTS],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        document = service.documents().get(documentId=doc_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Docs get failed for edit %r: %s", doc_id, exc)
        return {"ok": False, "error": f"Docs API error: {exc}", "document_id": doc_id}

    end_index = _end_index(document)
    requests: list[dict[str, Any]] = []
    if action == "replace":
        if end_index > 2:
            requests.append(
                {
                    "deleteContentRange": {
                        "range": {"startIndex": 1, "endIndex": end_index - 1}
                    }
                }
            )
        if text:
            requests.append({"insertText": {"location": {"index": 1}, "text": text}})
    elif text:
        insert_at = max(end_index - 1, 1)
        requests.append({"insertText": {"location": {"index": insert_at}, "text": text}})

    if requests:
        try:
            service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests},
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.info("Docs batchUpdate failed for %r: %s", doc_id, exc)
            return {"ok": False, "error": f"Docs API error: {exc}", "document_id": doc_id}

    refreshed = read_google_doc(doc_id, cfg=cfg)
    if not refreshed.get("ok"):
        return {
            "ok": True,
            "document_id": doc_id,
            "title": str(document.get("title") or ""),
            "mode": action,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit",
        }
    refreshed["mode"] = action
    refreshed["url"] = f"https://docs.google.com/document/d/{doc_id}/edit"
    return refreshed
