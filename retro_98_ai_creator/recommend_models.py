"""Recommend Text / Image / Video models for Control Panel from live catalogs."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

CRITERIA = ("economical", "balanced", "quality")

# Preference order when Google's catalog has no prices (first match in live list wins).
_GEMINI_PREFS: dict[str, dict[str, tuple[str, ...]]] = {
    "economical": {
        "text": (
            "gemini-2.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash",
            "gemini-flash-latest",
        ),
        "image": (
            "gemini-2.5-flash-image",
            "gemini-2.5-flash-preview-image-generation",
            "imagen-3.0-generate-002",
        ),
        "video": (
            "veo-2.0-generate-001",
            "veo-2.0-generate-exp",
            "veo-3.0-generate-001",
        ),
    },
    "balanced": {
        "text": (
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
        ),
        "image": (
            "gemini-2.5-flash-image",
            "gemini-2.5-flash-preview-image-generation",
            "gemini-3.1-flash-image-preview",
            "imagen-3.0-generate-002",
        ),
        "video": (
            "veo-2.0-generate-001",
            "veo-3.0-generate-001",
            "veo-3.1-generate-preview",
        ),
    },
    "quality": {
        "text": (
            "gemini-2.5-pro",
            "gemini-pro-latest",
            "gemini-2.5-flash",
            "gemini-flash-latest",
        ),
        "image": (
            "gemini-3.1-flash-image-preview",
            "imagen-4.0-generate-001",
            "imagen-3.0-generate-002",
            "gemini-2.5-flash-image",
        ),
        "video": (
            "veo-3.1-generate-preview",
            "veo-3.0-generate-001",
            "veo-2.0-generate-001",
        ),
    },
}

_HF_PREFS: dict[str, dict[str, tuple[str, ...]]] = {
    "economical": {
        "text": (
            "Qwen/Qwen2.5-1.5B-Instruct",
            "microsoft/Phi-3.5-mini-instruct",
            "google/gemma-2-2b-it",
            "Qwen/Qwen2.5-3B-Instruct",
        ),
        "image": (
            "stabilityai/sd-turbo",
            "stable-diffusion-v1-5/stable-diffusion-v1-5",
            "runwayml/stable-diffusion-v1-5",
        ),
        "video": (
            "cerspense/zeroscope_v2_576w",
            "ali-vilab/text-to-video-ms-1.7b",
            "damo-vilab/text-to-video-ms-1.7b",
        ),
    },
    "balanced": {
        "text": (
            "microsoft/Phi-3.5-mini-instruct",
            "Qwen/Qwen2.5-3B-Instruct",
            "google/gemma-2-2b-it",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ),
        "image": (
            "stable-diffusion-v1-5/stable-diffusion-v1-5",
            "stabilityai/sd-turbo",
            "stabilityai/sdxl-turbo",
            "runwayml/stable-diffusion-v1-5",
        ),
        "video": (
            "ali-vilab/text-to-video-ms-1.7b",
            "cerspense/zeroscope_v2_576w",
            "damo-vilab/text-to-video-ms-1.7b",
        ),
    },
    "quality": {
        "text": (
            "Qwen/Qwen2.5-7B-Instruct",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "microsoft/Phi-3.5-mini-instruct",
        ),
        "image": (
            "stabilityai/stable-diffusion-xl-base-1.0",
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/sdxl-turbo",
            "stable-diffusion-v1-5/stable-diffusion-v1-5",
        ),
        "video": (
            "Wan-AI/Wan2.1-T2V-1.3B",
            "THUDM/CogVideoX-2b",
            "ali-vilab/text-to-video-ms-1.7b",
            "cerspense/zeroscope_v2_576w",
        ),
    },
}


def normalize_criteria(value: str | None) -> str:
    raw = (value or "").strip().lower()
    aliases = {
        "economical": "economical",
        "economy": "economical",
        "budget": "economical",
        "cheap": "economical",
        "cheapest": "economical",
        "free": "economical",
        "best free": "economical",
        "best_free": "economical",
        "best-free": "economical",
        "lowest cost": "economical",
        "balanced": "balanced",
        "balance": "balanced",
        "recommended": "balanced",
        "everyday": "balanced",
        "quality": "quality",
        "maximum quality": "quality",
        "maximum_quality": "quality",
        "highest quality": "quality",
        "highest_quality": "quality",
        "premium": "quality",
        "best": "quality",
    }
    out = aliases.get(raw) or aliases.get(raw.replace(" ", "_"))
    if out not in CRITERIA:
        raise ValueError(
            "criteria must be one of: economical, balanced, quality (maximum quality)."
        )
    return out


def recommend_models_for_config(
    config: dict[str, Any],
    criteria: str,
    *,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Fetch live catalogs for the active backend and pick Text / Image / Video models.

    Returns ``{ok, provider, criteria, picks, models, labels, message}``.
    ``models`` is a merged picker list (live + picks) the UI should reload.
    """
    crit = normalize_criteria(criteria)
    raw_provider = (provider or "").strip().lower() or (
        ((config.get("backend") or {}).get("provider") or "gemini").lower().strip()
    )
    if raw_provider in ("google", "google-gemini"):
        raw_provider = "gemini"
    if raw_provider in ("open-router", "or"):
        raw_provider = "openrouter"
    if raw_provider in ("hf", "local", "phi"):
        raw_provider = "huggingface"

    if raw_provider == "gemini":
        return _recommend_gemini(config, crit)
    if raw_provider == "openrouter":
        return _recommend_openrouter(config, crit)
    if raw_provider == "huggingface":
        return _recommend_hf(config, crit)
    raise RuntimeError(f"Unknown provider for recommendations: {raw_provider}")


def _by_modality(models: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {"text": [], "image": [], "video": []}
    for item in models:
        mod = str(item.get("modality") or "text").lower()
        if mod in out:
            out[mod].append(item)
    return out


def _pick_from_prefs(
    available: list[dict[str, str]],
    prefs: tuple[str, ...],
) -> dict[str, str] | None:
    ids = {str(m.get("repo_id") or "").strip(): m for m in available}
    lower_map = {k.lower(): v for k, v in ids.items()}
    for pref in prefs:
        if pref in ids:
            return ids[pref]
        hit = lower_map.get(pref.lower())
        if hit:
            return hit
        # Substring fallback (e.g. prefer any *flash-lite*)
        for mid, row in ids.items():
            if pref.lower() in mid.lower():
                return row
    return available[0] if available else None


def _ensure_pick_in_models(
    models: list[dict[str, str]],
    picks: dict[str, str],
) -> list[dict[str, str]]:
    """Guarantee recommended ids appear in the picker list."""
    seen = {str(m.get("repo_id") or "").strip() for m in models}
    out = list(models)
    for mod, mid in picks.items():
        mid = (mid or "").strip()
        if not mid or mid in seen:
            continue
        seen.add(mid)
        out.append(
            {
                "repo_id": mid,
                "label": mid,
                "notes": "recommended",
                "modality": mod,
            }
        )
    return out


def _recommend_gemini(config: dict[str, Any], criteria: str) -> dict[str, Any]:
    from .gemini_provider import (
        DEFAULT_GEMINI_IMAGE_MODEL,
        DEFAULT_GEMINI_TEXT_MODEL,
        DEFAULT_GEMINI_VIDEO_MODEL,
        SUGGESTED_GEMINI_MODELS,
        list_available_gemini_models,
        resolve_api_key,
    )

    key = resolve_api_key(config.get("gemini") or {})
    source = "fallback"
    models: list[dict[str, str]]
    if key:
        try:
            models = list_available_gemini_models(key)
            source = "live"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini recommend list failed: %s", exc)
            models = list(SUGGESTED_GEMINI_MODELS)
    else:
        models = list(SUGGESTED_GEMINI_MODELS)

    buckets = _by_modality(models)
    prefs = _GEMINI_PREFS[criteria]
    defaults = {
        "text": DEFAULT_GEMINI_TEXT_MODEL,
        "image": DEFAULT_GEMINI_IMAGE_MODEL,
        "video": DEFAULT_GEMINI_VIDEO_MODEL,
    }
    picks: dict[str, str] = {}
    labels: dict[str, str] = {}
    for mod in ("text", "image", "video"):
        row = _pick_from_prefs(buckets[mod], prefs[mod])
        mid = (row or {}).get("repo_id") or defaults[mod]
        picks[mod] = mid
        labels[mod] = str((row or {}).get("label") or mid)

    models = _ensure_pick_in_models(models, picks)
    return {
        "ok": True,
        "provider": "gemini",
        "criteria": criteria,
        "source": source,
        "picks": picks,
        "labels": labels,
        "models": models,
        "message": _summary_message("Gemini", criteria, labels),
    }


def _openrouter_prompt_price(item: dict[str, Any]) -> float | None:
    pricing = item.get("pricing") or {}
    raw = pricing.get("prompt")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _openrouter_is_free(item: dict[str, Any]) -> bool:
    mid = str(item.get("id") or "").lower()
    if mid.endswith(":free") or ":free" in mid:
        return True
    price = _openrouter_prompt_price(item)
    return price is not None and price <= 0.0


def _recommend_openrouter(config: dict[str, Any], criteria: str) -> dict[str, Any]:
    from .openrouter_provider import (
        DEFAULT_OPENROUTER_IMAGE_MODEL,
        DEFAULT_OPENROUTER_TEXT_MODEL,
        DEFAULT_OPENROUTER_VIDEO_MODEL,
        OPENROUTER_BASE_URL,
        SUGGESTED_OPENROUTER_MODELS,
        _fetch_openrouter_models,
        _modality_from_openrouter_item,
        _openrouter_model_label,
        _openrouter_model_notes,
        merge_openrouter_model_suggestions,
        resolve_api_key,
    )

    cfg = config.get("openrouter") or {}
    api_key = resolve_api_key(cfg)
    base_url = (cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL

    live_rows: list[dict[str, str]] = []
    ranked: dict[str, list[dict[str, Any]]] = {"text": [], "image": [], "video": []}
    source = "fallback"

    try:
        for modality, output_tag in (
            ("text", "text"),
            ("image", "image"),
            ("video", "video"),
        ):
            raw_items = _fetch_openrouter_models(
                output_modality=output_tag,
                sort="most-popular",
                api_key=api_key,
                base_url=base_url,
            )
            for item in raw_items:
                mid = str(item.get("id") or "").strip()
                if not mid:
                    continue
                inferred = _modality_from_openrouter_item(item, fallback=modality)
                if inferred != modality:
                    continue
                ranked[modality].append(item)
                live_rows.append(
                    {
                        "repo_id": mid,
                        "label": _openrouter_model_label(mid, item.get("name")),
                        "notes": _openrouter_model_notes(item),
                        "modality": modality,
                    }
                )
        source = "live"
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenRouter recommend list failed: %s", exc)
        live_rows = []

    models = merge_openrouter_model_suggestions(live_rows, SUGGESTED_OPENROUTER_MODELS)
    buckets = _by_modality(models)
    defaults = {
        "text": DEFAULT_OPENROUTER_TEXT_MODEL,
        "image": DEFAULT_OPENROUTER_IMAGE_MODEL,
        "video": DEFAULT_OPENROUTER_VIDEO_MODEL,
    }
    picks: dict[str, str] = {}
    labels: dict[str, str] = {}

    for mod in ("text", "image", "video"):
        chosen = _pick_openrouter_item(ranked[mod], criteria)
        if chosen:
            mid = str(chosen.get("id") or "").strip()
            label = _openrouter_model_label(mid, chosen.get("name"))
        else:
            # Fall back to curated / merged picker list heuristics
            row = _pick_openrouter_fallback(buckets[mod], criteria) or (
                buckets[mod][0] if buckets[mod] else None
            )
            mid = str((row or {}).get("repo_id") or defaults[mod])
            label = str((row or {}).get("label") or mid)
        picks[mod] = mid
        labels[mod] = label

    models = _ensure_pick_in_models(models, picks)
    return {
        "ok": True,
        "provider": "openrouter",
        "criteria": criteria,
        "source": source,
        "picks": picks,
        "labels": labels,
        "models": models,
        "message": _summary_message("OpenRouter", criteria, labels),
    }


def _pick_openrouter_item(
    items: list[dict[str, Any]], criteria: str
) -> dict[str, Any] | None:
    if not items:
        return None
    if criteria == "economical":
        # Free first, else lowest prompt price
        free = [i for i in items if _openrouter_is_free(i)]
        if free:
            return free[0]
        priced: list[tuple[float, dict[str, Any]]] = []
        for item in items:
            p = _openrouter_prompt_price(item)
            if p is None:
                continue
            priced.append((p, item))
        if priced:
            priced.sort(key=lambda t: (t[0], str(t[1].get("id") or "")))
            return priced[0][1]
        return items[0]
    if criteria == "balanced":
        # Prefer popular non-free mid-tier (flash / mini / haiku), else first non-free
        balanced_re = re.compile(
            r"(flash(?!-lite)|mini|haiku|sonnet|gpt-4o-mini|gemini-2\.5-flash(?!-lite))",
            re.I,
        )
        for item in items:
            mid = str(item.get("id") or "")
            name = str(item.get("name") or "")
            if _openrouter_is_free(item):
                continue
            if balanced_re.search(mid) or balanced_re.search(name):
                return item
        for item in items:
            if not _openrouter_is_free(item):
                return item
        return items[0]
    # quality — first popular item that looks "pro"/flagship, else top popular
    quality_re = re.compile(
        r"(pro|opus|ultra|sonnet|gpt-4|o1|o3|claude-3|claude-4|gemini-2\.5-pro|veo-3)",
        re.I,
    )
    for item in items:
        mid = str(item.get("id") or "")
        name = str(item.get("name") or "")
        if quality_re.search(mid) or quality_re.search(name):
            if ":free" in mid.lower():
                continue
            return item
    for item in items:
        if not _openrouter_is_free(item):
            return item
    return items[0]


def _pick_openrouter_fallback(
    rows: list[dict[str, str]], criteria: str
) -> dict[str, str] | None:
    if not rows:
        return None
    if criteria == "economical":
        for row in rows:
            mid = str(row.get("repo_id") or "").lower()
            if ":free" in mid or "lite" in mid or mid.endswith("free"):
                return row
        return rows[0]
    if criteria == "balanced":
        balanced_re = re.compile(r"(flash(?!-lite)|mini|haiku|gemini-2\.5-flash)", re.I)
        for row in rows:
            mid = str(row.get("repo_id") or "")
            if ":free" in mid.lower():
                continue
            if balanced_re.search(mid):
                return row
        for row in rows:
            if ":free" not in str(row.get("repo_id") or "").lower():
                return row
        return rows[0]
    if criteria == "quality":
        quality_re = re.compile(r"(pro|opus|ultra|sonnet|gpt-4|veo-3)", re.I)
        for row in rows:
            if quality_re.search(str(row.get("repo_id") or "")):
                return row
    return rows[0]


def _recommend_hf(config: dict[str, Any], criteria: str) -> dict[str, Any]:
    from .config import (
        DEFAULT_HF_IMAGE_MODEL,
        DEFAULT_HF_TEXT_MODEL,
        DEFAULT_HF_VIDEO_MODEL,
        SUGGESTED_MODELS,
    )
    from .hf_provider import list_available_hf_models, merge_hf_model_suggestions

    source = "fallback"
    live: list[dict[str, str]] = []
    try:
        live = list_available_hf_models(
            config.get("huggingface") or {}, limit=40
        )
        source = "live"
    except Exception as exc:  # noqa: BLE001
        logger.warning("HF recommend list failed: %s", exc)

    models = merge_hf_model_suggestions(live, SUGGESTED_MODELS)
    buckets = _by_modality(models)
    prefs = _HF_PREFS[criteria]
    defaults = {
        "text": DEFAULT_HF_TEXT_MODEL,
        "image": DEFAULT_HF_IMAGE_MODEL,
        "video": DEFAULT_HF_VIDEO_MODEL,
    }
    picks: dict[str, str] = {}
    labels: dict[str, str] = {}
    for mod in ("text", "image", "video"):
        row = _pick_from_prefs(buckets[mod], prefs[mod])
        # For quality with live Hub data, prefer highest-download row if prefs miss
        if criteria == "quality" and buckets[mod] and not row:
            row = buckets[mod][0]
        mid = (row or {}).get("repo_id") or defaults[mod]
        picks[mod] = mid
        labels[mod] = str((row or {}).get("label") or mid)

    models = _ensure_pick_in_models(models, picks)
    return {
        "ok": True,
        "provider": "huggingface",
        "criteria": criteria,
        "source": source,
        "picks": picks,
        "labels": labels,
        "models": models,
        "message": _summary_message("Hugging Face", criteria, labels),
    }


def _summary_message(provider: str, criteria: str, labels: dict[str, str]) -> str:
    pretty = {
        "economical": "Economical",
        "balanced": "Balanced",
        "quality": "Maximum quality",
    }.get(criteria, criteria)
    return (
        f"{provider} · {pretty}: "
        f"text {labels.get('text') or '—'}, "
        f"image {labels.get('image') or '—'}, "
        f"video {labels.get('video') or '—'}"
    )
