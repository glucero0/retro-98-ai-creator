"""Tests for Google Calendar tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from unittest.mock import MagicMock, patch

from retro_98_ai_creator.calendar_client import (
    _event_time,
    create_calendar_event,
    edit_calendar_event,
    list_calendar_events,
)


def test_list_calendar_events_returns_items():
    service = MagicMock()
    service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "e1",
                "summary": "Standup",
                "start": {"dateTime": "2026-08-30T09:00:00-06:00"},
                "end": {"dateTime": "2026-08-30T09:30:00-06:00"},
                "htmlLink": "https://calendar.google.com/event?eid=e1",
                "status": "confirmed",
            }
        ]
    }
    with patch(
        "retro_98_ai_creator.calendar_client.build_google_service",
        return_value=service,
    ):
        result = list_calendar_events(time_min="2026-08-30T00:00:00Z")
    assert result["ok"] is True
    assert result["count"] == 1
    assert result["events"][0]["summary"] == "Standup"


def test_create_calendar_event_requires_fields():
    result = create_calendar_event("", "", "")
    assert result["ok"] is False
    assert "summary" in result["error"].lower()


def test_create_calendar_event_inserts():
    service = MagicMock()
    service.events.return_value.insert.return_value.execute.return_value = {
        "id": "e2",
        "summary": "Lunch",
        "start": {"dateTime": "2026-08-30T12:00:00-06:00"},
        "end": {"dateTime": "2026-08-30T13:00:00-06:00"},
        "htmlLink": "https://calendar.google.com/event?eid=e2",
        "status": "confirmed",
    }
    with patch(
        "retro_98_ai_creator.calendar_client.build_google_service",
        return_value=service,
    ):
        result = create_calendar_event(
            "Lunch",
            "2026-08-30T12:00:00-06:00",
            "2026-08-30T13:00:00-06:00",
        )
    assert result["ok"] is True
    assert result["id"] == "e2"
    body = service.events.return_value.insert.call_args.kwargs["body"]
    assert body["summary"] == "Lunch"


def test_edit_calendar_event_requires_id():
    result = edit_calendar_event("", summary="x")
    assert result["ok"] is False
    assert "event_id" in result["error"].lower()


class _NamedOffset(tzinfo):
    def __init__(self, offset: timedelta, key: str) -> None:
        self._offset = offset
        self.key = key

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return self._offset

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, dt: datetime | None) -> str:
        return self.key


def test_event_time_naive_stamp_gets_local_offset():
    frozen = datetime(
        2026, 8, 30, 7, 58, tzinfo=timezone(timedelta(hours=-6), "MDT")
    )
    result = _event_time("2026-09-02T09:45:00", all_day=False, now=frozen)
    assert result["dateTime"] == "2026-09-02T09:45:00-06:00"
    assert "timeZone" not in result


def test_event_time_naive_stamp_sets_iana_timezone():
    frozen = datetime(
        2026, 8, 30, 7, 58, tzinfo=_NamedOffset(timedelta(hours=-6), "America/Denver")
    )
    result = _event_time("2026-09-02T09:45:00", all_day=False, now=frozen)
    assert result["dateTime"] == "2026-09-02T09:45:00-06:00"
    assert result["timeZone"] == "America/Denver"


def test_event_time_preserves_zulu():
    result = _event_time("2026-09-02T09:45:00Z", all_day=False)
    assert result == {"dateTime": "2026-09-02T09:45:00Z"}


def test_event_time_preserves_existing_offset():
    result = _event_time("2026-09-02T09:45:00-06:00", all_day=False)
    assert result == {"dateTime": "2026-09-02T09:45:00-06:00"}


def test_create_calendar_event_naive_stamp_gets_offset():
    service = MagicMock()
    service.events.return_value.insert.return_value.execute.return_value = {
        "id": "e3",
        "summary": "Fire jim jim",
        "start": {"dateTime": "2026-09-02T09:45:00-06:00"},
        "end": {"dateTime": "2026-09-02T10:45:00-06:00"},
        "status": "confirmed",
    }
    with patch(
        "retro_98_ai_creator.calendar_client.build_google_service",
        return_value=service,
    ):
        result = create_calendar_event(
            "Fire jim jim",
            "2026-09-02T09:45:00",
            "2026-09-02T10:45:00",
        )
    assert result["ok"] is True
    body = service.events.return_value.insert.call_args.kwargs["body"]
    start = body["start"]["dateTime"]
    end = body["end"]["dateTime"]
    assert start.startswith("2026-09-02T09:45:00")
    assert end.startswith("2026-09-02T10:45:00")
    assert start != "2026-09-02T09:45:00"
    assert end != "2026-09-02T10:45:00"
