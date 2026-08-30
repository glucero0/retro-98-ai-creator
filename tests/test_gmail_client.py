"""Tests for Gmail search_gmail client."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from retro_98_ai_creator.gmail_client import (
    _extract_plain_body,
    authorize_gmail,
    get_gmail_credentials,
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
        "retro_98_ai_creator.gmail_client.build_google_service",
        side_effect=RuntimeError("Google Workspace is not authorized."),
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


def test_authorize_gmail_requests_offline_refresh_token(tmp_path: Path):
    creds_file = tmp_path / "client.json"
    creds_file.write_text("{}", encoding="utf-8")
    token = tmp_path / "token.json"
    cfg = {
        "gmail": {
            "credentials_path": str(creds_file),
            "token_path": str(token),
        }
    }
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"refresh_token": "rt"}'
    mock_creds.refresh_token = "rt"
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch(
        "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
        return_value=mock_flow,
    ):
        result = authorize_gmail(cfg)

    assert result["ok"] is True
    kwargs = mock_flow.run_local_server.call_args.kwargs
    assert kwargs["access_type"] == "offline"
    assert kwargs["prompt"] == "consent"
    assert kwargs["include_granted_scopes"] == "true"
    assert token.is_file()


def test_gmail_auth_status_unconfigured(tmp_path: Path):
    status = gmail_auth_status(
        {"gmail": {"token_path": str(tmp_path / "missing_token.json")}}
    )
    assert status["ok"] is True
    assert status["configured"] is False
    assert status["authorized"] is False
    assert status["has_refresh_token"] is False


def test_get_gmail_credentials_returns_none_when_refresh_fails(tmp_path: Path):
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    cfg = {"gmail": {"token_path": str(token)}}
    expired = MagicMock()
    expired.valid = False
    expired.refresh_token = "rt"

    with (
        patch(
            "retro_98_ai_creator.google_auth._load_stored_credentials",
            return_value=expired,
        ),
        patch(
            "retro_98_ai_creator.google_auth._refresh_credentials",
            side_effect=RuntimeError("invalid_grant"),
        ),
    ):
        assert get_gmail_credentials(cfg) is None
