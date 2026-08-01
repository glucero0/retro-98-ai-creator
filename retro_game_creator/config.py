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
ENV_PATH = PROJECT_ROOT / ".env"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_HF_MODEL = "microsoft/Phi-3.5-mini-instruct"
# Back-compat alias used by older tests / docs
DEFAULT_MODEL = DEFAULT_HF_MODEL

DEFAULTS: dict[str, Any] = {
    "backend": {
        # gemini (default, fast API) | huggingface (local, optional deps)
        "provider": "gemini",
    },
    "gemini": {
        "model": DEFAULT_GEMINI_MODEL,
        "api_key": None,  # prefer GEMINI_API_KEY in .env
        "google_search": True,
        "temperature": 0.4,
    },
    "model": {
        "repo_id": DEFAULT_HF_MODEL,
        "revision": "main",
        "device": "auto",
        "torch_dtype": "auto",
        "max_new_tokens": 2048,
        "temperature": 0.4,
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
        "default_preset": None,
        "default_theme": "auto",
        "window_width": 1280,
        "window_height": 800,
        "title": "Game Base Ref Creator 98",
    },
    "paths": {
        # Relative paths resolve against the project root
        "archives": "archives.json",
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


def _write_env_key(key: str, value: str) -> None:
    """Set or replace a KEY=value line in the project .env (create if needed)."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    prefix = f"{key}="
    replaced = False
    out: list[str] = []
    for line in lines:
        if line.strip().startswith(prefix) or line.strip().startswith(f"# {prefix}"):
            if not replaced:
                out.append(f"{key}={value}")
                replaced = True
            continue
        out.append(line)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


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

    # Remap retired Gemini model IDs still saved in older configs
    from .gemini_provider import normalize_gemini_model

    gemini = cfg.setdefault("gemini", {})
    gemini["model"] = normalize_gemini_model(gemini.get("model"))
    return cfg


def save_config(updates: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Persist Control Panel changes to the project config.yaml (keys go to .env)."""
    current = existing or load_config()
    updates = copy.deepcopy(updates)

    gemini_updates = updates.get("gemini")
    if isinstance(gemini_updates, dict):
        incoming = (gemini_updates.get("api_key") or "").strip()
        if incoming:
            _write_env_key("GEMINI_API_KEY", incoming)
            import os

            os.environ["GEMINI_API_KEY"] = incoming
        gemini_updates = dict(gemini_updates)
        gemini_updates.pop("api_key", None)
        updates["gemini"] = gemini_updates

    merged = _deep_merge(current, updates)
    paths = merged.setdefault("paths", {})
    paths.pop("user_config", None)

    # Never persist secrets in config.yaml — use .env
    gemini_out = dict(merged.get("gemini") or {})
    gemini_out["api_key"] = None

    to_write = {
        "backend": merged.get("backend", {}),
        "gemini": gemini_out,
        "model": merged["model"],
        "generation": merged["generation"],
        "ui": merged["ui"],
        "paths": {
            "archives": paths.get("archives") or DEFAULTS["paths"]["archives"],
        },
    }
    with DEFAULT_CONFIG_PATH.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(to_write, fh, default_flow_style=False, sort_keys=False)

    merged["gemini"] = gemini_out
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
        "notes": "~3.8B params — local, no API key",
    },
    {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct",
        "label": "Qwen2.5 3B Instruct",
        "notes": "Strong small instruct model",
    },
    {
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5 1.5B Instruct",
        "notes": "Faster / lower memory",
    },
    {
        "repo_id": "google/gemma-2-2b-it",
        "label": "Gemma 2 2B IT",
        "notes": "Compact Gemma instruct (may require HF acceptance)",
    },
]
