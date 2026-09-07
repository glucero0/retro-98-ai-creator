"""Generation router — Google Gemini."""

from __future__ import annotations

import logging
from typing import Any, Callable

from .creation_utils import is_generic_studio_request
from .modality import check_prompt_model_compatibility
from .presets import resolve_creation_description

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]


def _active_model_and_provider(config: dict[str, Any]) -> tuple[str, str]:
    from .gemini_provider import normalize_gemini_model

    g = config.get("gemini") or {}
    return normalize_gemini_model(g.get("text_model")), "gemini"


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
    basis_media: dict[str, Any] | None = None,
    tool_aliases: list[str] | None = None,
    search_query: str | None = None,
) -> dict[str, Any]:
    """Dispatch to Gemini and return a creation document."""
    from .cancellation import raise_if_cancelled
    from .gemini_provider import generate_with_gemini
    from .modality import infer_prompt_modality

    def _cancelled() -> bool:
        return bool(cancel_event is not None and cancel_event.is_set())

    raise_if_cancelled(_cancelled)

    generic = is_generic_studio_request(game, platform, creation_type)
    # Known franchise base names → Search Results without spending an LLM call
    if not exact_title and not generic:
        from .franchise_disambiguation import maybe_raise_franchise_ambiguous

        maybe_raise_franchise_ambiguous(game)

    system_extra = (config.get("prompt") or {}).get("extra_instructions", "") or ""
    creation_description = resolve_creation_description(
        creation_type,
        game,
        platform,
        override=creation_description,
    )
    search_text = (search_query or "").strip() or None

    basis = basis_media if isinstance(basis_media, dict) else None
    basis_mod = ""
    if basis:
        basis_mod = str(basis.get("modality") or "").strip().lower()
        if basis_mod not in {"image", "video"}:
            basis_mod = ""

    from .modality import resolve_generation_modality

    # Prompt intent wins (e.g. "generate a video" + image basis → I2V).
    # Ambiguous prompts with a media basis keep the basis modality.
    forced_modality = resolve_generation_modality(
        creation_description or game,
        basis_modality=basis_mod or None,
        layout_basis=bool(basis and basis.get("extracted_layout")),
    )
    if basis and basis.get("extracted_layout"):
        from .extract_layout import format_layout_basis_prompt

        creation_description = format_layout_basis_prompt(
            basis.get("extracted_layout"),
            existing=creation_description or "",
        )
    prompt_for_compat = creation_description or game
    if forced_modality == "image" and not infer_prompt_modality(prompt_for_compat):
        prompt_for_compat = f"Create an image: {prompt_for_compat}"
    elif forced_modality == "video" and not infer_prompt_modality(prompt_for_compat):
        prompt_for_compat = f"Generate a video: {prompt_for_compat}"
    elif forced_modality == "audio" and not infer_prompt_modality(prompt_for_compat):
        prompt_for_compat = f"Generate music: {prompt_for_compat}"

    model_id, provider = _active_model_and_provider(config)
    compat = check_prompt_model_compatibility(
        prompt_for_compat,
        model_id,
        provider=provider,
        gemini_cfg=config.get("gemini"),
    )
    if not compat.get("ok"):
        raise RuntimeError(compat.get("error") or "Model modality mismatch.")

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
        basis_media=basis,
        forced_modality=forced_modality,
        cancel_event=cancel_event,
        tool_aliases=tool_aliases,
        search_query=search_text,
    )


def provider_status(config: dict[str, Any]) -> dict[str, Any]:
    """Status line for Control Panel / Studio."""
    from .gemini_provider import resolve_api_key

    g = config.get("gemini") or {}
    has_key = bool(resolve_api_key(g))
    text_m = g.get("text_model")
    image_m = g.get("image_model")
    video_m = g.get("video_model")
    audio_m = g.get("audio_model")
    detail = (
        f"Gemini ready · text {text_m} · image {image_m} · video {video_m} · audio {audio_m}"
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
        "audioModel": audio_m,
        "modality": "multi",
        "device": "api",
    }
