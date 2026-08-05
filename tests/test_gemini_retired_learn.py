"""Self-healing Gemini retired-model detection and persistence."""

from __future__ import annotations

from retro_98_ai_creator.gemini_provider import (
    extract_model_from_gemini_error,
    is_retired_gemini_error,
    learn_retired_gemini_model,
    merged_retired_aliases,
    normalize_gemini_model,
)


def test_detect_retired_404_message():
    err = (
        "Gemini API error: 404 NOT_FOUND. {'error': {'code': 404, "
        "'message': 'This model models/gemini-2.5-flash-lite is no longer "
        "available to new users. Please update your code to use a newer model "
        "for the latest features and improvements.', 'status': 'NOT_FOUND'}}"
    )
    assert is_retired_gemini_error(err)
    assert extract_model_from_gemini_error(err) == "gemini-2.5-flash-lite"


def test_detect_ignores_unrelated_errors():
    assert not is_retired_gemini_error("OpenRouter HTTP 400: bad request")
    assert not is_retired_gemini_error("network timeout")


def test_learn_retired_persists_and_switches_slot(tmp_path, monkeypatch):
    from retro_98_ai_creator import config as config_mod

    monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", tmp_path / "config.yaml")
    cfg = {
        "backend": {"provider": "gemini"},
        "gemini": {
            "text_model": "gemini-mystery-flash",
            "image_model": "gemini-2.5-flash-image",
            "video_model": "veo-2.0-generate-001",
            "retired_model_aliases": {},
        },
        "ui": {},
        "paths": {"archives": str(tmp_path / "archives.json")},
        "prompt": {},
        "openrouter": {},
        "huggingface": {},
    }

    info = learn_retired_gemini_model(cfg, "gemini-mystery-flash")
    assert info["retired"] == "gemini-mystery-flash"
    assert info["switched"] is True
    assert info["replacement"] == "gemini-2.5-flash"
    assert info["config"]["gemini"]["text_model"] == "gemini-2.5-flash"
    assert (
        info["config"]["gemini"]["retired_model_aliases"]["gemini-mystery-flash"]
        == "gemini-2.5-flash"
    )

    aliases = merged_retired_aliases(info["config"]["gemini"])
    assert normalize_gemini_model(
        "gemini-mystery-flash", retired_aliases=aliases
    ) == "gemini-2.5-flash"


def test_merged_aliases_learned_override_builtin():
    cfg = {
        "retired_model_aliases": {
            "gemini-2.5-flash-lite": "gemini-2.5-flash",  # custom override
        }
    }
    aliases = merged_retired_aliases(cfg)
    assert aliases["gemini-2.5-flash-lite"] == "gemini-2.5-flash"


def test_suggested_list_includes_veo_31_fast():
    from retro_98_ai_creator.gemini_provider import SUGGESTED_GEMINI_MODELS

    ids = {m["repo_id"] for m in SUGGESTED_GEMINI_MODELS}
    assert "veo-3.1-fast-generate-preview" in ids


def test_bootstrap_exposes_retired_and_keeps_veo_fast(tmp_path, monkeypatch):
    import retro_98_ai_creator.api as api_mod
    from retro_98_ai_creator.api import Api

    cfg = {
        "backend": {"provider": "gemini"},
        "gemini": {
            "text_model": "gemini-2.5-flash",
            "image_model": "gemini-2.5-flash-image",
            "video_model": "veo-3.1-fast-generate-preview",
            "retired_model_aliases": {"gemini-mystery-flash": "gemini-2.5-flash"},
        },
        "ui": {},
        "paths": {"archives": str(tmp_path / "archives.json")},
        "prompt": {},
        "openrouter": {},
        "huggingface": {},
    }
    monkeypatch.setattr(api_mod, "load_config", lambda: cfg)
    api = Api()
    api.config = cfg
    boot = api.get_bootstrap()
    assert "gemini-mystery-flash" in boot["retiredGeminiModels"]
    suggested_ids = {m["repo_id"] for m in boot["suggestedGeminiModels"]}
    assert "veo-3.1-fast-generate-preview" in suggested_ids
    assert boot["config"]["gemini"]["video_model"] == "veo-3.1-fast-generate-preview"
