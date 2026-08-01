"""Generation router — Gemini (default) or local Hugging Face."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]


def generate_creation(
    game: str,
    platform: str,
    creation_type: str,
    config: dict[str, Any],
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Dispatch to the configured backend and return a creation document."""
    backend = ((config.get("backend") or {}).get("provider") or "gemini").lower().strip()
    system_extra = (config.get("generation") or {}).get("system_extra", "") or ""

    if backend in ("gemini", "google", "google-gemini"):
        from .gemini_provider import generate_with_gemini

        return generate_with_gemini(
            game,
            platform,
            creation_type,
            gemini_cfg=config.get("gemini") or {},
            system_extra=system_extra,
            progress=progress,
        )

    if backend in ("huggingface", "hf", "local", "phi"):
        from .llm import model_manager

        model_manager.set_progress_callback(progress)
        return model_manager.generate_creation(
            game=game,
            platform=platform,
            creation_type=creation_type,
            model_cfg=config.get("model") or {},
            system_extra=system_extra,
        )

    raise RuntimeError(
        f"Unknown backend provider {backend!r}. Use 'gemini' or 'huggingface'."
    )


def provider_status(config: dict[str, Any]) -> dict[str, Any]:
    """Status line for Control Panel / Studio."""
    backend = ((config.get("backend") or {}).get("provider") or "gemini").lower()
    if backend in ("gemini", "google", "google-gemini"):
        from .gemini_provider import normalize_gemini_model, resolve_api_key

        g = config.get("gemini") or {}
        has_key = bool(resolve_api_key(g))
        model = normalize_gemini_model(g.get("model"))
        return {
            "state": "ready" if has_key else "needs_key",
            "detail": (
                f"Gemini ready ({model})"
                if has_key
                else "Set GEMINI_API_KEY or paste key in Control Panel"
            ),
            "provider": "gemini",
            "loaded_repo": model,
            "device": "api",
        }

    from .llm import model_manager

    status = dict(model_manager.status)
    status["provider"] = "huggingface"
    return status
