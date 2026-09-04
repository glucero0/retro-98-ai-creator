"""Recommend Text / Image / Video models for Control Panel from live catalogs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

CRITERIA = ("economical", "balanced", "quality")

# Preference order when Google's catalog has no prices (first match in live list wins).
_GEMINI_PREFS: dict[str, dict[str, tuple[str, ...]]] = {
    "economical": {
        "text": (
            "gemini-3.1-flash-lite",
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
            "gemini-3.1-flash-lite",
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
    Fetch Gemini's live catalog and pick Text / Image / Video models.

    Returns ``{ok, provider, criteria, picks, models, labels, message}``.
    ``models`` is a merged picker list (live + picks) the UI should reload.
    ``provider`` is ignored (Gemini-only).
    """
    crit = normalize_criteria(criteria)
    _ = provider
    return _recommend_gemini(config, crit)


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
        merged_retired_aliases,
        normalize_gemini_model,
        resolve_api_key,
    )

    key = resolve_api_key(config.get("gemini") or {})
    aliases = merged_retired_aliases(config.get("gemini") or {})
    source = "fallback"
    models: list[dict[str, str]]
    if key:
        try:
            models = list_available_gemini_models(key, retired_aliases=aliases)
            source = "live"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini recommend list failed: %s", exc)
            models = [
                m
                for m in SUGGESTED_GEMINI_MODELS
                if (m.get("repo_id") or "").lower() not in {k.lower() for k in aliases}
            ]
    else:
        models = [
            m
            for m in SUGGESTED_GEMINI_MODELS
            if (m.get("repo_id") or "").lower() not in {k.lower() for k in aliases}
        ]

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
        mid = normalize_gemini_model(
            (row or {}).get("repo_id") or defaults[mod],
            retired_aliases=aliases,
        )
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
