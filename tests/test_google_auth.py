"""Tests for shared Google OAuth helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from retro_98_ai_creator.google_auth import (
    DEFAULT_TOKEN_REL,
    DRIVE_READONLY,
    GMAIL_MODIFY,
    GMAIL_READONLY,
    GOOGLE_SCOPES,
    authorize_google,
    get_google_credentials,
    google_auth_status,
    granted_products,
    has_scope,
    token_path,
)


def test_has_scope_accepts_gmail_modify_for_readonly():
    creds = SimpleNamespace(scopes=[GMAIL_MODIFY])
    assert has_scope(creds, GMAIL_READONLY) is True
    assert has_scope(creds, DRIVE_READONLY) is False


def test_granted_products_from_subset():
    creds = SimpleNamespace(scopes=[GMAIL_READONLY, DRIVE_READONLY])
    assert granted_products(creds) == ["Gmail", "Drive"]


def test_token_path_rewrites_legacy_gmail_filename():
    path = token_path(
        {"google_workspace": {"token_path": ".retro-98-ai-creator/gmail_token.json"}}
    )
    assert path.name == "google_workspace_token.json"
    assert DEFAULT_TOKEN_REL.endswith("google_workspace_token.json")
    path = token_path(
        {"google_workspace": {"token_path": r"C:\data\gmail_token.json"}}
    )
    assert path.name == "google_workspace_token.json"


def test_google_auth_status_unconfigured(tmp_path: Path):
    status = google_auth_status(
        {"google_workspace": {"token_path": str(tmp_path / "missing_token.json")}}
    )
    assert status["ok"] is True
    assert status["configured"] is False
    assert status["authorized"] is False
    assert status["granted_products"] == []
    assert status["requested_scopes"] == list(GOOGLE_SCOPES)


def test_authorize_google_requires_credentials_path():
    result = authorize_google({"gmail": {"credentials_path": None}})
    assert result["ok"] is False
    assert "not set" in result["error"].lower()


def test_get_google_credentials_requires_requested_scope(tmp_path: Path):
    token = tmp_path / "token.json"
    token.write_text("{}", encoding="utf-8")
    cfg = {"gmail": {"token_path": str(token)}}
    creds = MagicMock()
    creds.valid = True
    creds.scopes = [GMAIL_READONLY]

    with patch(
        "retro_98_ai_creator.google_auth._load_stored_credentials",
        return_value=creds,
    ):
        assert get_google_credentials(cfg) is creds
        assert (
            get_google_credentials(cfg, required_scopes=[DRIVE_READONLY]) is None
        )
