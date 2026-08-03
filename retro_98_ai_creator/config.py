"""Configuration loading and persistence."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config.example.yaml"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_GEMINI_VIDEO_MODEL = "veo-2.0-generate-001"
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
DEFAULT_HF_MODEL = "microsoft/Phi-3.5-mini-instruct"
# Back-compat alias used by older tests / docs
DEFAULT_MODEL = DEFAULT_HF_MODEL

DEFAULTS: dict[str, Any] = {
    "backend": {
        # gemini (default) | openrouter | huggingface (local, optional deps)
        "provider": "gemini",
    },
    "gemini": {
        # Legacy single-model key — kept in sync with text_model
        "model": DEFAULT_GEMINI_TEXT_MODEL,
        "text_model": DEFAULT_GEMINI_TEXT_MODEL,
        "image_model": DEFAULT_GEMINI_IMAGE_MODEL,
        "video_model": DEFAULT_GEMINI_VIDEO_MODEL,
        "api_key": None,  # set via Control Panel → saved in config.yaml
        "google_search": True,
        # When google_search is on: Pass 1 extract + Pass 2 verify at temperature 0
        "two_pass_verify": True,
        "temperature": 0.0,
    },
    "openrouter": {
        "model": DEFAULT_OPENROUTER_MODEL,
        "api_key": None,  # set via Control Panel → saved in config.yaml
        "temperature": 0.0,
        "base_url": "https://openrouter.ai/api/v1",
    },
    "model": {
        "repo_id": DEFAULT_HF_MODEL,
        "revision": "main",
        "device": "auto",
        "torch_dtype": "auto",
        "max_new_tokens": 2048,
        "temperature": 0.0,
        "top_p": 0.9,
        "trust_remote_code": False,
        "hf_token": None,
    },
    "generation": {
        "system_extra": "",
    },
    "ui": {
        "sound_enabled": True,
        "crt_enabled": False,
        "ui_scale": 1.0,
        "default_platform": None,
        "default_theme": "auto",
        "app_theme": "light",
        "custom_theme": {
            "desktop_color": "#008080",
            "window_color": "#c0c0c0",
            "title_color": "#000080",
            "text_color": "#222222",
            "font": "sans",
        },
        "window_width": 1280,
        "window_height": 800,
        "title": "Retro 98 AI Creator",
    },
    "paths": {
        # Relative paths resolve against the project root
        "archives": "archives.json",
        "media": "media",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def expand_path(path_str: str) -> Path:
    """Resolve ~ and relative paths (relative → project root)."""
    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config at {path} must be a mapping")
    return data


def load_config() -> dict[str, Any]:
    """Merge defaults ← config.yaml ← optional config.local.yaml."""
    cfg = copy.deepcopy(DEFAULTS)

    for path in (DEFAULT_CONFIG_PATH, PROJECT_ROOT / "config.local.yaml"):
        cfg = _deep_merge(cfg, _load_yaml(path))

    # Drop legacy home-dir path keys if present in older files
    paths = cfg.setdefault("paths", {})
    paths.pop("user_config", None)
    if not paths.get("archives"):
        paths["archives"] = DEFAULTS["paths"]["archives"]
    if not paths.get("media"):
        paths["media"] = DEFAULTS["paths"]["media"]

    # Drop retired Game Defaults key (preset → platform)
    ui = cfg.setdefault("ui", {})
    ui.pop("default_preset", None)

    # Remap / migrate Gemini model settings (legacy single model → three slots)
    from .gemini_provider import migrate_gemini_model_config, normalize_gemini_model

    gemini = cfg.setdefault("gemini", {})
    migrate_gemini_model_config(gemini)
    gemini["model"] = normalize_gemini_model(gemini.get("model") or gemini.get("text_model"))
    gemini["text_model"] = normalize_gemini_model(gemini.get("text_model"))
    gemini["image_model"] = normalize_gemini_model(gemini.get("image_model"))
    gemini["video_model"] = normalize_gemini_model(gemini.get("video_model"))
    return cfg


def _apply_api_key_update(updates: dict[str, Any], section: str) -> None:
    """Blank api_key fields mean keep the existing key (do not clear)."""
    section_updates = updates.get(section)
    if not isinstance(section_updates, dict):
        return
    incoming = (section_updates.get("api_key") or "").strip()
    section_updates = dict(section_updates)
    if incoming:
        section_updates["api_key"] = incoming
    else:
        section_updates.pop("api_key", None)
    updates[section] = section_updates


def _normalize_api_key(section: dict[str, Any]) -> dict[str, Any]:
    out = dict(section or {})
    raw_key = (out.get("api_key") or "").strip()
    out["api_key"] = raw_key or None
    return out


def save_config(updates: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Persist Control Panel changes to the project config.yaml."""
    current = existing or load_config()
    updates = copy.deepcopy(updates)

    _apply_api_key_update(updates, "gemini")
    _apply_api_key_update(updates, "openrouter")

    merged = _deep_merge(current, updates)
    paths = merged.setdefault("paths", {})
    paths.pop("user_config", None)
    ui_out = dict(merged.get("ui") or {})
    ui_out.pop("default_preset", None)

    gemini_out = _normalize_api_key(merged.get("gemini") or {})
    openrouter_out = _normalize_api_key(merged.get("openrouter") or {})

    to_write = {
        "backend": merged.get("backend", {}),
        "gemini": gemini_out,
        "openrouter": openrouter_out,
        "model": merged["model"],
        "generation": merged["generation"],
        "ui": ui_out,
        "paths": {
            "archives": paths.get("archives") or DEFAULTS["paths"]["archives"],
        },
    }
    with DEFAULT_CONFIG_PATH.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(to_write, fh, default_flow_style=False, sort_keys=False)

    merged["gemini"] = gemini_out
    merged["openrouter"] = openrouter_out
    merged["ui"] = ui_out
    return merged


# Back-compat aliases
save_user_config = save_config


def archives_path(cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    return expand_path(cfg["paths"]["archives"])


# Suggested Hugging Face models (local backend)
SUGGESTED_MODELS: list[dict[str, str]] = [
    {
        "repo_id": "microsoft/Phi-3.5-mini-instruct",
        "label": "Phi-3.5 Mini Instruct",
        "notes": "~3.8B — often weak for accurate docs (needs 70B+ / MCP search)",
    },
    {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct",
        "label": "Qwen2.5 3B Instruct",
        "notes": "Small local — not recommended for keybindings without search tools",
    },
    {
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5 1.5B Instruct",
        "notes": "Fastest / lowest memory — demos only",
    },
    {
        "repo_id": "google/gemma-2-2b-it",
        "label": "Gemma 2 2B IT",
        "notes": "Compact (may require HF acceptance) — demos only",
    },
]
