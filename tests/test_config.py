"""Basic config merge / defaults."""

from pathlib import Path

from retro_98_ai_creator.config import (
    DEFAULT_HF_MODEL,
    DEFAULTS,
    PROJECT_ROOT,
    archives_path,
    expand_path,
    load_config,
)
from retro_98_ai_creator.creation_utils import extract_json_object
from retro_98_ai_creator.gemini_provider import normalize_gemini_model


def test_default_backend_is_gemini():
    assert DEFAULTS["backend"]["provider"] == "gemini"
    assert DEFAULTS["gemini"]["model"] == "gemini-2.5-flash"


def test_hf_default_still_phi35():
    assert DEFAULT_HF_MODEL == "microsoft/Phi-3.5-mini-instruct"
    assert DEFAULTS["model"]["repo_id"] == DEFAULT_HF_MODEL


def test_load_config_has_sections():
    cfg = load_config()
    assert "backend" in cfg
    assert "gemini" in cfg
    assert "model" in cfg
    assert "user_config" not in (cfg.get("paths") or {})


def test_archives_path_is_in_project():
    path = archives_path(load_config())
    assert path == (PROJECT_ROOT / "archives.json").resolve()


def test_relative_expand_path_uses_project_root():
    assert expand_path("archives.json") == (PROJECT_ROOT / "archives.json").resolve()
    assert expand_path(str(Path.home() / "x.json")).is_absolute()


def test_extract_json_still_works():
    assert extract_json_object('{"game": "Doom"}')["game"] == "Doom"


def test_deprecated_gemini_models_remap():
    assert normalize_gemini_model("gemini-2.0-flash") == "gemini-2.5-flash"
    assert normalize_gemini_model("models/gemini-2.0-flash") == "gemini-2.5-flash"
    assert normalize_gemini_model("gemini-2.5-flash") == "gemini-2.5-flash"


def test_ui_app_theme_defaults():
    ui = DEFAULTS["ui"]
    assert ui["app_theme"] == "light"
    custom = ui["custom_theme"]
    assert custom["desktop_color"] == "#008080"
    assert custom["window_color"] == "#c0c0c0"
    assert custom["title_color"] == "#000080"
    assert custom["text_color"] == "#222222"
    assert custom["font"] == "sans"


def test_load_config_preserves_app_theme_keys():
    cfg = load_config()
    ui = cfg.get("ui") or {}
    assert "app_theme" in ui
    assert ui["app_theme"] in {"light", "dark", "custom"} or isinstance(
        ui["app_theme"], str
    )
    custom = ui.get("custom_theme") or {}
    for key in (
        "desktop_color",
        "window_color",
        "title_color",
        "text_color",
        "font",
    ):
        assert key in custom
