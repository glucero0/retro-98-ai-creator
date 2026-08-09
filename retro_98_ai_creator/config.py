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

DEFAULT_GEMINI_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_GEMINI_VIDEO_MODEL = "veo-2.0-generate-001"
DEFAULT_OPENROUTER_TEXT_MODEL = "google/gemini-2.5-flash"
DEFAULT_OPENROUTER_IMAGE_MODEL = "google/gemini-2.5-flash-image"
DEFAULT_OPENROUTER_VIDEO_MODEL = "google/veo-2.0"
DEFAULT_HF_TEXT_MODEL = "microsoft/Phi-3.5-mini-instruct"
DEFAULT_HF_IMAGE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_HF_VIDEO_MODEL = "ali-vilab/text-to-video-ms-1.7b"
# Back-compat alias (older configs / imports used a single text repo)
DEFAULT_HF_MODEL = DEFAULT_HF_TEXT_MODEL

DEFAULTS: dict[str, Any] = {
    "backend": {
        # gemini (default) | openrouter | huggingface (local, optional deps)
        "provider": "gemini",
    },
    "gemini": {
        "text_model": DEFAULT_GEMINI_TEXT_MODEL,
        "image_model": DEFAULT_GEMINI_IMAGE_MODEL,
        "video_model": DEFAULT_GEMINI_VIDEO_MODEL,
        "api_key": None,  # set via Control Panel → saved in config.yaml
        "google_search": True,
        # When google_search is on: Pass 1 extract + Pass 2 verify at temperature 0
        "two_pass_verify": True,
        # Local file tools via Gemini function calling (can combine with google_search)
        "use_tools": False,
        # When google_search is on: OCR images / YouTube captions from cited search results
        "ocr_search_images": True,
        "youtube_search_captions": True,
        "temperature": 0.0,
        # Runtime-learned: { "old-model-id": "replacement-id" } merged with built-ins
        "retired_model_aliases": {},
    },
    "openrouter": {
        "text_model": DEFAULT_OPENROUTER_TEXT_MODEL,
        "image_model": DEFAULT_OPENROUTER_IMAGE_MODEL,
        "video_model": DEFAULT_OPENROUTER_VIDEO_MODEL,
        "api_key": None,  # set via Control Panel → saved in config.yaml
        "temperature": 0.0,
        "base_url": "https://openrouter.ai/api/v1",
    },
    "huggingface": {
        # Three modality slots — Studio picks by prompt intent (like Gemini/OpenRouter)
        "text_model": DEFAULT_HF_TEXT_MODEL,
        "image_model": DEFAULT_HF_IMAGE_MODEL,
        "video_model": DEFAULT_HF_VIDEO_MODEL,
        # Alias of text_model (kept for older configs / UI)
        "repo_id": DEFAULT_HF_TEXT_MODEL,
        "revision": "main",
        "device": "auto",
        "torch_dtype": "auto",
        "max_new_tokens": 2048,
        "temperature": 0.0,
        "top_p": 0.9,
        "trust_remote_code": False,
        "hf_token": None,
    },
    "prompt": {
        # Appended to generation prompts (Control Panel → Extra system instructions)
        "extra_instructions": "",
    },
    "ui": {
        "sound_enabled": True,
        "sound_volume": 100,
        "crt_enabled": False,
        "ui_scale": 1.0,
        "ui_font": "inter",
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
    "gmail": {
        # OAuth client JSON from Google Cloud (Desktop app) — set via Control Panel
        "credentials_path": None,
        # Authorized-user token (gitignored under .retro-98-ai-creator/)
        "token_path": ".retro-98-ai-creator/gmail_token.json",
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


def normalize_huggingface_cfg(hf: dict[str, Any] | None) -> dict[str, Any]:
    """
    Normalize Hugging Face settings to three modality slots.

    Older configs only had ``repo_id`` (text). That value becomes ``text_model``
    when ``text_model`` is missing; ``repo_id`` stays synced as an alias.
    """
    out = dict(hf or {})
    text = (
        (out.get("text_model") or out.get("repo_id") or DEFAULT_HF_TEXT_MODEL) or ""
    ).strip() or DEFAULT_HF_TEXT_MODEL
    image = (
        (out.get("image_model") or DEFAULT_HF_IMAGE_MODEL) or ""
    ).strip() or DEFAULT_HF_IMAGE_MODEL
    video = (
        (out.get("video_model") or DEFAULT_HF_VIDEO_MODEL) or ""
    ).strip() or DEFAULT_HF_VIDEO_MODEL
    out["text_model"] = text
    out["image_model"] = image
    out["video_model"] = video
    out["repo_id"] = text
    return out


def normalize_gemini_cfg(section: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize Gemini keys and remap shut-down model ids."""
    from .gemini_provider import (
        DEFAULT_GEMINI_IMAGE_MODEL,
        DEFAULT_GEMINI_TEXT_MODEL,
        DEFAULT_GEMINI_VIDEO_MODEL,
        _gemini_model_id,
        learned_retired_aliases,
        merged_retired_aliases,
        normalize_gemini_model,
    )

    out = dict(section or {})
    raw_key = (out.get("api_key") or "").strip()
    out["api_key"] = raw_key or None
    aliases = merged_retired_aliases(out)
    text = normalize_gemini_model(
        out.get("text_model") or DEFAULT_GEMINI_TEXT_MODEL,
        retired_aliases=aliases,
    )
    image_raw = _gemini_model_id(out.get("image_model") or DEFAULT_GEMINI_IMAGE_MODEL)
    image = (
        aliases.get(image_raw)
        or aliases.get(image_raw.lower())
        or image_raw
        or DEFAULT_GEMINI_IMAGE_MODEL
    )
    video = _gemini_model_id(out.get("video_model") or "") or DEFAULT_GEMINI_VIDEO_MODEL
    video = aliases.get(video) or aliases.get(video.lower()) or video
    out["text_model"] = text
    out["image_model"] = image
    out["video_model"] = video
    out["retired_model_aliases"] = learned_retired_aliases(out)
    return out


def load_config() -> dict[str, Any]:
    """Merge defaults ← config.yaml ← optional config.local.yaml."""
    cfg = copy.deepcopy(DEFAULTS)

    for path in (DEFAULT_CONFIG_PATH, PROJECT_ROOT / "config.local.yaml"):
        cfg = _deep_merge(cfg, _load_yaml(path))

    cfg["huggingface"] = normalize_huggingface_cfg(cfg.get("huggingface"))
    cfg["gemini"] = normalize_gemini_cfg(cfg.get("gemini"))

    paths = cfg.setdefault("paths", {})
    if not paths.get("archives"):
        paths["archives"] = DEFAULTS["paths"]["archives"]
    if not paths.get("media"):
        paths["media"] = DEFAULTS["paths"]["media"]
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
    ui_out = dict(merged.get("ui") or {})

    gemini_out = normalize_gemini_cfg(merged.get("gemini") or {})
    openrouter_out = _normalize_api_key(merged.get("openrouter") or {})
    huggingface_out = normalize_huggingface_cfg(merged.get("huggingface") or {})
    prompt_out = dict(merged.get("prompt") or {})
    prompt_out.setdefault("extra_instructions", "")
    gmail_out = dict(merged.get("gmail") or {})
    gmail_out.setdefault("token_path", DEFAULTS["gmail"]["token_path"])

    to_write = {
        "backend": merged.get("backend", {}),
        "gemini": gemini_out,
        "openrouter": openrouter_out,
        "huggingface": huggingface_out,
        "prompt": prompt_out,
        "gmail": gmail_out,
        "ui": ui_out,
        "paths": {
            "archives": paths.get("archives") or DEFAULTS["paths"]["archives"],
        },
    }
    with DEFAULT_CONFIG_PATH.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(to_write, fh, default_flow_style=False, sort_keys=False)

    merged["gemini"] = gemini_out
    merged["openrouter"] = openrouter_out
    merged["huggingface"] = huggingface_out
    merged["prompt"] = prompt_out
    merged["gmail"] = gmail_out
    merged["ui"] = ui_out
    return merged


def archives_path(cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    return expand_path(cfg["paths"]["archives"])

# Suggested Hugging Face models (local backend) — curated per modality
SUGGESTED_MODELS: list[dict[str, str]] = [
    {
        "repo_id": "microsoft/Phi-3.5-mini-instruct",
        "label": "Phi-3.5 Mini Instruct",
        "notes": "~3.8B text — weak for accurate docs without search tools",
        "modality": "text",
    },
    {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct",
        "label": "Qwen2.5 3B Instruct",
        "notes": "Small local text — demos / light writing",
        "modality": "text",
    },
    {
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "label": "Qwen2.5 1.5B Instruct",
        "notes": "Fastest / lowest VRAM text — demos only",
        "modality": "text",
    },
    {
        "repo_id": "google/gemma-2-2b-it",
        "label": "Gemma 2 2B IT",
        "notes": "Compact text (may require HF acceptance)",
        "modality": "text",
    },
    {
        "repo_id": "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "label": "Stable Diffusion 1.5",
        "notes": "Classic local text-to-image (~4GB VRAM typical)",
        "modality": "image",
    },
    {
        "repo_id": "stabilityai/sd-turbo",
        "label": "SD Turbo",
        "notes": "Fast image (1–4 steps) — higher VRAM than SD 1.5",
        "modality": "image",
    },
    {
        "repo_id": "stabilityai/sdxl-turbo",
        "label": "SDXL Turbo",
        "notes": "Higher quality turbo image — needs more VRAM",
        "modality": "image",
    },
    {
        "repo_id": "ali-vilab/text-to-video-ms-1.7b",
        "label": "ModelScope Text-to-Video 1.7B",
        "notes": "Classic Diffusers T2V — short clips, heavy on CPU/GPU",
        "modality": "video",
    },
    {
        "repo_id": "cerspense/zeroscope_v2_576w",
        "label": "Zeroscope v2 576w",
        "notes": "Local text-to-video — short 576p-ish clips",
        "modality": "video",
    },
]
