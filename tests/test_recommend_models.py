"""Tests for Control Panel Recommend Models ranking helpers."""

from __future__ import annotations

import pytest

from retro_98_ai_creator.recommend_models import (
    _by_modality,
    _pick_from_prefs,
    normalize_criteria,
    recommend_models_for_config,
)


def test_normalize_criteria_aliases():
    assert normalize_criteria("Economical") == "economical"
    assert normalize_criteria("cheapest") == "economical"
    assert normalize_criteria("best free") == "economical"
    assert normalize_criteria("Balanced") == "balanced"
    assert normalize_criteria("recommended") == "balanced"
    assert normalize_criteria("Maximum quality") == "quality"
    assert normalize_criteria("highest quality") == "quality"
    with pytest.raises(ValueError):
        normalize_criteria("nope")


def test_pick_from_prefs_prefers_listed_id():
    rows = [
        {"repo_id": "gemini-2.5-flash", "label": "Flash", "modality": "text"},
        {"repo_id": "gemini-3.1-flash-lite", "label": "Lite", "modality": "text"},
        {"repo_id": "gemini-2.5-pro", "label": "Pro", "modality": "text"},
    ]
    picked = _pick_from_prefs(rows, ("gemini-3.1-flash-lite", "gemini-2.5-flash"))
    assert picked["repo_id"] == "gemini-3.1-flash-lite"


def test_recommend_gemini_uses_suggested_without_key(monkeypatch):
    cfg = {"backend": {"provider": "gemini"}, "gemini": {}}
    res = recommend_models_for_config(cfg, "balanced", provider="gemini")
    assert res["ok"] is True
    assert res["provider"] == "gemini"
    assert res["criteria"] == "balanced"
    assert res["picks"]["text"]
    assert res["picks"]["image"]
    assert res["picks"]["video"]
    mods = _by_modality(res["models"])
    assert any(m["repo_id"] == res["picks"]["text"] for m in mods["text"])


def test_recommend_gemini_economical_avoids_retired_flash_lite():
    cfg = {"backend": {"provider": "gemini"}, "gemini": {}}
    res = recommend_models_for_config(cfg, "economical", provider="gemini")
    assert res["ok"] is True
    assert res["picks"]["text"] == "gemini-3.1-flash-lite"
    assert "2.5-flash-lite" not in res["picks"]["text"]


def test_recommend_ignores_other_provider_names():
    cfg = {"backend": {"provider": "huggingface"}, "gemini": {}}
    res = recommend_models_for_config(cfg, "balanced", provider="openrouter")
    assert res["ok"] is True
    assert res["provider"] == "gemini"
