"""Google Calendar list / create / edit for Gemini tools."""

from __future__ import annotations

import logging
from typing import Any

from .google_auth import CALENDAR_EVENTS, build_google_service

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 20
MAX_RESULTS_CAP = 50
DEFAULT_CALENDAR = "primary"


def _normalize_max_results(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_RESULTS
    if n < 1:
        n = 1
    return min(n, MAX_RESULTS_CAP)


def _calendar_id(value: str | None) -> str:
    raw = (value or "").strip()
    return raw or DEFAULT_CALENDAR


def _event_summary(item: dict[str, Any]) -> dict[str, Any]:
    start = item.get("start") or {}
    end = item.get("end") or {}
    return {
        "id": str(item.get("id") or ""),
        "summary": str(item.get("summary") or ""),
        "description": str(item.get("description") or ""),
        "location": str(item.get("location") or ""),
        "start": str(start.get("dateTime") or start.get("date") or ""),
        "end": str(end.get("dateTime") or end.get("date") or ""),
        "html_link": str(item.get("htmlLink") or ""),
        "status": str(item.get("status") or ""),
    }


def _event_time(value: str, *, all_day: bool) -> dict[str, str]:
    stamp = (value or "").strip()
    if all_day:
        return {"date": stamp[:10]}
    return {"dateTime": stamp}


def list_calendar_events(
    *,
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int | None = None,
    calendar_id: str | None = None,
    query: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List upcoming events on a calendar (default: primary)."""
    limit = _normalize_max_results(
        max_results if max_results is not None else DEFAULT_MAX_RESULTS
    )
    cal = _calendar_id(calendar_id)
    try:
        service = build_google_service(
            "calendar",
            "v3",
            cfg,
            required_scopes=[CALENDAR_EVENTS],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    params: dict[str, Any] = {
        "calendarId": cal,
        "maxResults": limit,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if (time_min or "").strip():
        params["timeMin"] = time_min.strip()
    if (time_max or "").strip():
        params["timeMax"] = time_max.strip()
    if (query or "").strip():
        params["q"] = query.strip()

    try:
        listed = service.events().list(**params).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Calendar list failed: %s", exc)
        return {"ok": False, "error": f"Calendar API error: {exc}"}

    events = [_event_summary(item) for item in listed.get("items") or []]
    return {
        "ok": True,
        "calendar_id": cal,
        "count": len(events),
        "events": events,
    }


def create_calendar_event(
    summary: str,
    start: str,
    end: str,
    *,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str | None = None,
    all_day: bool = False,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = (summary or "").strip()
    if not title:
        return {"ok": False, "error": "summary is required"}
    if not (start or "").strip() or not (end or "").strip():
        return {
            "ok": False,
            "error": "start and end are required (RFC3339 dateTime, or YYYY-MM-DD when all_day)",
        }

    cal = _calendar_id(calendar_id)
    try:
        service = build_google_service(
            "calendar",
            "v3",
            cfg,
            required_scopes=[CALENDAR_EVENTS],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    body: dict[str, Any] = {
        "summary": title,
        "start": _event_time(start, all_day=all_day),
        "end": _event_time(end, all_day=all_day),
    }
    if description is not None:
        body["description"] = str(description)
    if location is not None:
        body["location"] = str(location)

    try:
        created = service.events().insert(calendarId=cal, body=body).execute()
    except Exception as exc:  # noqa: BLE001
        logger.info("Calendar insert failed: %s", exc)
        return {"ok": False, "error": f"Calendar API error: {exc}"}

    out = _event_summary(created)
    out["ok"] = True
    out["calendar_id"] = cal
    return out


def edit_calendar_event(
    event_id: str,
    *,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str | None = None,
    all_day: bool = False,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    eid = (event_id or "").strip()
    if not eid:
        return {"ok": False, "error": "event_id is required"}

    body: dict[str, Any] = {}
    if summary is not None:
        body["summary"] = str(summary)
    if description is not None:
        body["description"] = str(description)
    if location is not None:
        body["location"] = str(location)
    if start is not None:
        body["start"] = _event_time(start, all_day=all_day)
    if end is not None:
        body["end"] = _event_time(end, all_day=all_day)
    if not body:
        return {"ok": False, "error": "provide at least one field to update"}

    cal = _calendar_id(calendar_id)
    try:
        service = build_google_service(
            "calendar",
            "v3",
            cfg,
            required_scopes=[CALENDAR_EVENTS],
        )
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}

    try:
        updated = (
            service.events()
            .patch(calendarId=cal, eventId=eid, body=body)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("Calendar patch failed for %r: %s", eid, exc)
        return {"ok": False, "error": f"Calendar API error: {exc}", "event_id": eid}

    out = _event_summary(updated)
    out["ok"] = True
    out["calendar_id"] = cal
    return out
