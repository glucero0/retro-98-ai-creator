"""Tests for Gmail search_gmail client."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from retro_98_ai_creator.gmail_client import (
    _extract_plain_body,
    authorize_gmail,
    gmail_auth_status,
    search_gmail,
)


def test_extract_plain_body_from_simple_payload():
    text = "Hello inbox"
    data = base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
    payload = {"mimeType": "text/plain", "body": {"data": data}}
    assert _extract_plain_body(payload) == text


def test_search_gmail_requires_query():
    result = search_gmail("")
    assert result["ok"] is False
    assert "query" in result["error"].lower()


def test_search_gmail_not_authorized():
    cfg = {
        "gmail": {
            "credentials_path": None,
            "token_path": ".retro-98-ai-creator/gmail_token.json",
        }
    }
    with patch(
        "retro_98_ai_creator.gmail_client.get_gmail_credentials",
        return_value=None,
    ):
        result = search_gmail("is:unread", cfg=cfg)
    assert result["ok"] is False
    assert "not authorized" in result["error"].lower()


def test_search_gmail_returns_messages(tmp_path: Path):
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    cfg = {
        "gmail": {
            "credentials_path": str(tmp_path / "client.json"),
            "token_path": str(token),
        }
    }

    listed = {"messages": [{"id": "m1"}], "resultSizeEstimate": 1}
    detail = {
        "id": "m1",
        "threadId": "t1",
        "snippet": "Your package shipped",
        "labelIds": ["UNREAD", "INBOX"],
        "payload": {
            "headers": [
                {"name": "From", "value": "shop@example.com"},
                {"name": "Subject", "value": "Shipment update"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 00:00:00 +0000"},
            ]
        },
    }

    service = MagicMock()
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = listed
    service.users.return_value.messages.return_value.get.return_value.execute.return_value = detail

    with patch(
        "retro_98_ai_creator.gmail_client._build_gmail_service",
        return_value=service,
    ):
        result = search_gmail("is:unread", max_results=5, cfg=cfg)

    assert result["ok"] is True
    assert result["query"] == "is:unread"
    assert result["count"] == 1
    msg = result["messages"][0]
    assert msg["subject"] == "Shipment update"
    assert msg["is_unread"] is True
    assert msg["body"] is None


def test_authorize_gmail_requires_credentials_path():
    result = authorize_gmail({"gmail": {"credentials_path": None}})
    assert result["ok"] is False
    assert "not set" in result["error"].lower()


def test_gmail_auth_status_unconfigured():
    status = gmail_auth_status({"gmail": {}})
    assert status["ok"] is True
    assert status["configured"] is False
    assert status["authorized"] is False
