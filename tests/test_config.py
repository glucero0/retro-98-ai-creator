"""Basic config merge / defaults."""

from pathlib import Path

from retro_game_creator.config import (
    DEFAULT_HF_MODEL,
    DEFAULTS,
    PROJECT_ROOT,
    archives_path,
    expand_path,
    load_config,
)
from retro_game_creator.creation_utils import extract_json_object
from retro_game_creator.gemini_provider import normalize_gemini_model


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
