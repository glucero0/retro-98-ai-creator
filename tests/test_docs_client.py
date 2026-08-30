"""Tests for Google Docs tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retro_98_ai_creator.docs_client import (
    create_google_doc,
    edit_google_doc,
    read_google_doc,
)


def _doc_payload(title: str = "Doc", text: str = "Hello\n") -> dict:
    return {
        "title": title,
        "documentId": "d1",
        "revisionId": "r1",
        "body": {
            "content": [
                {
                    "endIndex": 1 + len(text),
                    "paragraph": {
                        "elements": [{"textRun": {"content": text}}],
                    },
                }
            ]
        },
    }


def test_read_google_doc_requires_id():
    result = read_google_doc("")
    assert result["ok"] is False
    assert "document_id" in result["error"].lower()


def test_read_google_doc_extracts_text():
    service = MagicMock()
    service.documents.return_value.get.return_value.execute.return_value = _doc_payload()
    with patch(
        "retro_98_ai_creator.docs_client.build_google_service",
        return_value=service,
    ):
        result = read_google_doc("d1")
    assert result["ok"] is True
    assert result["title"] == "Doc"
    assert result["text"] == "Hello\n"


def test_create_google_doc_requires_title():
    result = create_google_doc("")
    assert result["ok"] is False
    assert "title" in result["error"].lower()


def test_edit_google_doc_replace():
    service = MagicMock()
    service.documents.return_value.get.return_value.execute.return_value = _doc_payload(
        text="Old\n"
    )
    service.documents.return_value.batchUpdate.return_value.execute.return_value = {}
    with patch(
        "retro_98_ai_creator.docs_client.build_google_service",
        return_value=service,
    ):
        result = edit_google_doc("d1", text="New", mode="replace")
    assert result["ok"] is True
    assert result["mode"] == "replace"
    service.documents.return_value.batchUpdate.assert_called_once()
    body = service.documents.return_value.batchUpdate.call_args.kwargs["body"]
    assert "deleteContentRange" in body["requests"][0]
    assert body["requests"][1]["insertText"]["text"] == "New"
