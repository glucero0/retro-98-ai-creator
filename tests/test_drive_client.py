"""Tests for Google Drive tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retro_98_ai_creator.drive_client import create_drive_file, search_drive


def test_search_drive_requires_query():
    result = search_drive("")
    assert result["ok"] is False
    assert "query" in result["error"].lower()


def test_search_drive_returns_files():
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "f1",
                "name": "Budget",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-08-30T00:00:00Z",
                "webViewLink": "https://docs.google.com/document/d/f1/edit",
                "parents": ["root"],
            }
        ]
    }
    with patch(
        "retro_98_ai_creator.drive_client.build_google_service",
        return_value=service,
    ):
        result = search_drive("name contains 'Budget'", max_results=5)

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["files"][0]["id"] == "f1"
    assert result["files"][0]["name"] == "Budget"


def test_create_drive_file_requires_name():
    result = create_drive_file("")
    assert result["ok"] is False
    assert "name" in result["error"].lower()


def test_create_drive_file_uploads_text():
    service = MagicMock()
    service.files.return_value.create.return_value.execute.return_value = {
        "id": "f2",
        "name": "note.txt",
        "mimeType": "text/plain",
        "webViewLink": "https://drive.google.com/file/d/f2/view",
    }
    with (
        patch(
            "retro_98_ai_creator.drive_client.build_google_service",
            return_value=service,
        ),
        patch("googleapiclient.http.MediaInMemoryUpload", return_value=MagicMock()),
    ):
        result = create_drive_file("note.txt", content="hello")

    assert result["ok"] is True
    assert result["id"] == "f2"
    assert result["bytes_written"] == 5
