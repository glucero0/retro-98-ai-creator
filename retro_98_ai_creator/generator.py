"""Generation router — Gemini (default), OpenRouter, or local Hugging Face."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .creation_utils import is_generic_studio_request
from .modality import check_prompt_model_compatibility, classify_model_modality
from .presets import resolve_creation_description

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]


def _active_model_and_provider(config: dict[str, Any]) -> tuple[str, str]:
    backend = ((config.get("backend") or {}).get("provider") or "gemini").lower().strip()
    if backend in ("gemini", "google", "google-gemini"):
        from .gemini_provider import migrate_gemini_model_config, normalize_gemini_model

        g = migrate_gemini_model_config(dict(config.get("gemini") or {}))
        return normalize_gemini_model(g.get("text_model") or g.get("model")), "gemini"
    if backend in ("openrouter", "open-router", "or"):
        from .openrouter_provider import normalize_openrouter_model

        return (
            normalize_openrouter_model((config.get("openrouter") or {}).get("model")),
            "openrouter",
        )
    model = ((config.get("model") or {}).get("repo_id") or "").strip()
    return model, "huggingface"


def generate_creation(
    game: str,
    platform: str,
    creation_type: str,
    config: dict[str, Any],
    progress: ProgressCallback | None = None,
    *,
    exact_title: bool = False,
    creation_description: str | None = None,
    cancel_event: Any = None,
) -> dict[str, Any]:
    """Dispatch to the configured backend and return a creation document."""
    from .cancellation import raise_if_cancelled

    def _cancelled() -> bool:
        return bool(cancel_event is not None and cancel_event.is_set())

    raise_if_cancelled(_cancelled)

    generic = is_generic_studio_request(game, platform, creation_type)
    # Known franchise base names → Search Results without spending an LLM call
    if not exact_title and not generic:
        from .franchise_disambiguation import maybe_raise_franchise_ambiguous

        maybe_raise_franchise_ambiguous(game)

    backend = ((config.get("backend") or {}).get("provider") or "gemini").lower().strip()
    system_extra = (config.get("generation") or {}).get("system_extra", "") or ""
    creation_description = resolve_creation_description(
        creation_type,
        game,
        platform,
        override=creation_description,
    )

    # Prompt intent vs backend (Gemini routes by slot; OR/HF text-only)
    model_id, provider = _active_model_and_provider(config)
    compat = check_prompt_model_compatibility(
        creation_description or game,
        model_id,
        provider=provider,
        gemini_cfg=config.get("gemini") if provider == "gemini" else None,
    )
    if not compat.get("ok"):
        raise RuntimeError(compat.get("error") or "Model modality mismatch.")

    if backend in ("gemini", "google", "google-gemini"):
        from .gemini_provider import generate_with_gemini

        raise_if_cancelled(_cancelled)
        return generate_with_gemini(
            game,
            platform,
            creation_type,
            gemini_cfg=config.get("gemini") or {},
            system_extra=system_extra,
            creation_description=creation_description,
            progress=progress,
            exact_title=exact_title or generic,
        )

    if backend in ("openrouter", "open-router", "or"):
        from .openrouter_provider import generate_with_openrouter

        # OpenRouter curated list is chat/text; image/video stay on Gemini for now
        model = ((config.get("openrouter") or {}).get("model") or "")
        modality = classify_model_modality(model) or "text"
        if modality in {"image", "video"}:
            raise RuntimeError(
                f"OpenRouter model {model!r} looks like {modality}, but image/video "
                "generation is currently supported via the Gemini provider. "
                "Switch Provider to Google Gemini and pick an image or Veo model."
            )

        raise_if_cancelled(_cancelled)
        return generate_with_openrouter(
            game,
            platform,
            creation_type,
            openrouter_cfg=config.get("openrouter") or {},
            system_extra=system_extra,
            creation_description=creation_description,
            progress=progress,
            exact_title=exact_title or generic,
        )

    if backend in ("huggingface", "hf", "local", "phi"):
        from .llm import model_manager

        model_manager.set_progress_callback(progress)
        model_manager.set_cancel_event(cancel_event)
        try:
            raise_if_cancelled(_cancelled)
            return model_manager.generate_creation(
                game=game,
                platform=platform,
                creation_type=creation_type,
                model_cfg=config.get("model") or {},
                system_extra=system_extra,
                creation_description=creation_description,
                exact_title=exact_title or generic,
            )
        finally:
            model_manager.set_cancel_event(None)

    raise RuntimeError(
        f"Unknown backend provider {backend!r}. Use 'gemini', 'openrouter', or 'huggingface'."
    )


def provider_status(config: dict[str, Any]) -> dict[str, Any]:
    """Status line for Control Panel / Studio."""
    backend = ((config.get("backend") or {}).get("provider") or "gemini").lower()
    if backend in ("gemini", "google", "google-gemini"):
        from .gemini_provider import (
            migrate_gemini_model_config,
            resolve_api_key,
        )

        g = migrate_gemini_model_config(dict(config.get("gemini") or {}))
        has_key = bool(resolve_api_key(g))
        text_m = g.get("text_model") or g.get("model")
        image_m = g.get("image_model")
        video_m = g.get("video_model")
        detail = (
            f"Gemini ready · text {text_m} · image {image_m} · video {video_m}"
            if has_key
            else "Paste your Gemini API key in Control Panel"
        )
        return {
            "state": "ready" if has_key else "needs_key",
            "detail": detail,
            "provider": "gemini",
            "loaded_repo": text_m,
            "textModel": text_m,
            "imageModel": image_m,
            "videoModel": video_m,
            "modality": "multi",
            "device": "api",
        }

    if backend in ("openrouter", "open-router", "or"):
        from .openrouter_provider import normalize_openrouter_model, resolve_api_key

        o = config.get("openrouter") or {}
        has_key = bool(resolve_api_key(o))
        model = normalize_openrouter_model(o.get("model"))
        return {
            "state": "ready" if has_key else "needs_key",
            "detail": (
                f"OpenRouter ready ({model})"
                if has_key
                else "Paste your OpenRouter API key in Control Panel"
            ),
            "provider": "openrouter",
            "loaded_repo": model,
            "modality": "text",
            "device": "api",
        }

    from .llm import model_manager

    status = dict(model_manager.status)
    status["provider"] = "huggingface"
    status.setdefault("modality", "text")
    return status
