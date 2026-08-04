"""Gemini / OpenRouter modality model resolution."""

from retro_98_ai_creator.gemini_provider import (
    DEFAULT_GEMINI_IMAGE_MODEL,
    DEFAULT_GEMINI_TEXT_MODEL,
    DEFAULT_GEMINI_VIDEO_MODEL,
    resolve_gemini_model_for_modality,
)
from retro_98_ai_creator.openrouter_provider import (
    resolve_openrouter_model_for_modality,
)


def test_resolve_gemini_modality_slots():
    cfg = {
        "text_model": "gemini-2.5-pro",
        "image_model": "gemini-3.1-flash-image-preview",
        "video_model": "veo-3.1-generate-preview",
    }
    assert resolve_gemini_model_for_modality(cfg, "text") == "gemini-2.5-pro"
    assert (
        resolve_gemini_model_for_modality(cfg, "image")
        == "gemini-3.1-flash-image-preview"
    )
    assert resolve_gemini_model_for_modality(cfg, "video") == "veo-3.1-generate-preview"


def test_resolve_gemini_defaults_when_empty():
    assert resolve_gemini_model_for_modality({}, "text") == DEFAULT_GEMINI_TEXT_MODEL
    assert resolve_gemini_model_for_modality({}, "image") == DEFAULT_GEMINI_IMAGE_MODEL
    assert resolve_gemini_model_for_modality({}, "video") == DEFAULT_GEMINI_VIDEO_MODEL


def test_resolve_openrouter_modality_slots():
    cfg = {
        "text_model": "openai/gpt-4o",
        "image_model": "black-forest-labs/flux.2-pro",
        "video_model": "google/veo-3.1",
    }
    assert resolve_openrouter_model_for_modality(cfg, "text") == "openai/gpt-4o"
    assert (
        resolve_openrouter_model_for_modality(cfg, "image")
        == "black-forest-labs/flux.2-pro"
    )
    assert resolve_openrouter_model_for_modality(cfg, "video") == "google/veo-3.1"
