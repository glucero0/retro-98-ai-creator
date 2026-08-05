"""Tests for Control Panel Recommend Models ranking helpers."""

from __future__ import annotations

import pytest

from retro_98_ai_creator.recommend_models import (
    _by_modality,
    _openrouter_is_free,
    _pick_from_prefs,
    _pick_openrouter_item,
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


def test_openrouter_economical_balanced_quality_picks():
    items = [
        {
            "id": "vendor/big-pro",
            "name": "Big Pro",
            "pricing": {"prompt": "0.000005"},
        },
        {
            "id": "vendor/tiny:free",
            "name": "Tiny Free",
            "pricing": {"prompt": "0"},
        },
        {
            "id": "google/gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "pricing": {"prompt": "0.000001"},
        },
        {
            "id": "vendor/mid",
            "name": "Mid",
            "pricing": {"prompt": "0.000002"},
        },
    ]
    assert _openrouter_is_free(items[1]) is True
    economical = _pick_openrouter_item(items, "economical")
    assert economical["id"] == "vendor/tiny:free"
    balanced = _pick_openrouter_item(items, "balanced")
    assert balanced["id"] == "google/gemini-2.5-flash"
    quality = _pick_openrouter_item(items, "quality")
    assert quality["id"] == "vendor/big-pro"


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


def test_recommend_hf_quality_pref(monkeypatch):
    cfg = {"backend": {"provider": "huggingface"}, "huggingface": {}}

    def boom(*_a, **_k):
        raise RuntimeError("offline")

    monkeypatch.setattr(
        "retro_98_ai_creator.hf_provider.list_available_hf_models",
        boom,
    )
    res = recommend_models_for_config(cfg, "quality", provider="huggingface")
    assert res["ok"] is True
    assert res["source"] == "fallback"
    assert res["picks"]["text"]
