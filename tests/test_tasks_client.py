"""Tests for Google Tasks tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from synthetic_text_extruder.tasks_client import (
    _normalize_due,
    create_task,
    edit_task,
    list_tasks,
)


def test_list_tasks_returns_items():
    service = MagicMock()
    service.tasks.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "t1",
                "title": "Buy milk",
                "notes": "2%",
                "status": "needsAction",
                "due": "2026-08-30T00:00:00.000Z",
            }
        ]
    }
    with patch(
        "synthetic_text_extruder.tasks_client.build_google_service",
        return_value=service,
    ):
        result = list_tasks(query="milk")
    assert result["ok"] is True
    assert result["count"] == 1
    assert result["tasks"][0]["title"] == "Buy milk"


def test_create_task_requires_title():
    result = create_task("")
    assert result["ok"] is False
    assert "title" in result["error"].lower()


def test_create_task_inserts():
    service = MagicMock()
    service.tasks.return_value.insert.return_value.execute.return_value = {
        "id": "t2",
        "title": "Call Sam",
        "status": "needsAction",
    }
    with patch(
        "synthetic_text_extruder.tasks_client.build_google_service",
        return_value=service,
    ):
        result = create_task("Call Sam")
    assert result["ok"] is True
    assert result["id"] == "t2"
    body = service.tasks.return_value.insert.call_args.kwargs["body"]
    assert body["title"] == "Call Sam"


def test_edit_task_requires_id():
    result = edit_task("", title="x")
    assert result["ok"] is False
    assert "task_id" in result["error"].lower()


def test_edit_task_rejects_bad_status():
    result = edit_task("t1", status="done")
    assert result["ok"] is False
    assert "status" in result["error"].lower()


def test_normalize_due_naive_stamp_gets_local_offset():
    frozen = datetime(
        2026, 8, 30, 7, 58, tzinfo=timezone(timedelta(hours=-6), "MDT")
    )
    assert _normalize_due("2026-09-02T09:45:00", now=frozen) == (
        "2026-09-02T09:45:00-06:00"
    )
