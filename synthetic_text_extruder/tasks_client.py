"""Google Tasks list / create / edit for Gemini tools."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from .google_auth import TASKS, build_google_service

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 20
MAX_RESULTS_CAP = 50
DEFAULT_TASKLIST = "@default"

# Offset or Z after a time component (not the YYYY-MM-DD dashes).
_TZ_SUFFIX_RE = re.compile(r"(Z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)
_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _normalize_max_results(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_RESULTS
    if n < 1:
        n = 1
    return min(n, MAX_RESULTS_CAP)


def _tasklist_id(value: str | None) -> str:
    raw = (value or "").strip()
    return raw or DEFAULT_TASKLIST


def _offset_string(when: datetime) -> str:
    delta = when.utcoffset() or timedelta(0)
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _normalize_due(value: str, now: datetime | None = None) -> str:
    """Attach the local UTC offset to naive due stamps (never invent Z)."""
    stamp = (value or "").strip()
    if not stamp:
        return stamp
    if _TZ_SUFFIX_RE.search(stamp):
        return stamp
    if now is None:
        when = datetime.now().astimezone()
    else:
        when = now if now.tzinfo is not None else now.astimezone()
    offset = _offset_string(when)
    if _DATE_ONLY_RE.fullmatch(stamp):
        return f"{stamp}T00:00:00{offset}"
    return stamp + offset


def _task_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "notes": str(item.get("notes") or ""),
        "status": str(item.get("status") or ""),
        "due": str(item.get("due") or ""),
        "updated": str(item.get("updated") or ""),
        "completed": str(item.get("completed") or ""),
        "parent": str(item.get("parent") or ""),
        "position": str(item.get("position") or ""),
    }


def _build_service(cfg: dict[str, Any] | None = None) -> Any:
    return build_google_service(
        "tasks",
        "v1",
        cfg,
        required_scopes=[TASKS],
    )


def list_tasks(
    *,
    max_results: int | None = None,
    tasklist_id: str | None = None,
    show_completed: bool = False,
    query: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List tasks on a list (default: the user's default task list)."""
    limit = _normalize_max_results(
        max_results if max_results is not None else DEFAULT_MAX_RESULTS
    )
    list_id = _tasklist_id(tasklist_id)
    try:
        service = _build_service(cfg)
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    params: dict[str, Any] = {
        "tasklist": list_id,
        "maxResults": limit,
        "showCompleted": bool(show_completed),
        "showHidden": bool(show_completed),
    }
    try:
        listed = service.tasks().list(**params).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Tasks list failed: %s", exc)
        return {"ok": False, "error": f"Tasks API error: {exc}"}

    items = [_task_summary(item) for item in listed.get("items") or []]
    needle = (query or "").strip().lower()
    if needle:
        items = [
            item
            for item in items
            if needle in item["title"].lower() or needle in item["notes"].lower()
        ]
    return {
        "ok": True,
        "tasklist_id": list_id,
        "count": len(items),
        "tasks": items,
    }


def create_task(
    title: str,
    *,
    notes: str | None = None,
    due: str | None = None,
    tasklist_id: str | None = None,
    cfg: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    name = (title or "").strip()
    if not name:
        return {"ok": False, "error": "title is required"}

    list_id = _tasklist_id(tasklist_id)
    body: dict[str, Any] = {"title": name}
    if notes is not None:
        body["notes"] = str(notes)
    if (due or "").strip():
        body["due"] = _normalize_due(due.strip(), now=now)

    try:
        service = _build_service(cfg)
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        created = service.tasks().insert(tasklist=list_id, body=body).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Tasks insert failed: %s", exc)
        return {"ok": False, "error": f"Tasks API error: {exc}"}

    out = _task_summary(created)
    out["ok"] = True
    out["tasklist_id"] = list_id
    return out


def edit_task(
    task_id: str,
    *,
    title: str | None = None,
    notes: str | None = None,
    due: str | None = None,
    status: str | None = None,
    tasklist_id: str | None = None,
    cfg: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    tid = (task_id or "").strip()
    if not tid:
        return {"ok": False, "error": "task_id is required"}

    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = str(title)
    if notes is not None:
        body["notes"] = str(notes)
    if due is not None:
        body["due"] = _normalize_due(str(due).strip(), now=now)
    if status is not None:
        raw = str(status).strip()
        if raw not in {"needsAction", "completed"}:
            return {
                "ok": False,
                "error": "status must be 'needsAction' or 'completed'",
            }
        body["status"] = raw
    if not body:
        return {"ok": False, "error": "provide at least one field to update"}

    list_id = _tasklist_id(tasklist_id)
    try:
        service = _build_service(cfg)
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        updated = (
            service.tasks()
            .patch(tasklist=list_id, task=tid, body=body)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("Tasks patch failed for %r: %s", tid, exc)
        return {"ok": False, "error": f"Tasks API error: {exc}", "task_id": tid}

    out = _task_summary(updated)
    out["ok"] = True
    out["tasklist_id"] = list_id
    return out
