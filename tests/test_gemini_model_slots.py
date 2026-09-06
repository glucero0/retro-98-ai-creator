"""Gemini modality model resolution."""

from retro_98_ai_creator.gemini_provider import (
    DEFAULT_GEMINI_AUDIO_MODEL,
    DEFAULT_GEMINI_IMAGE_MODEL,
    DEFAULT_GEMINI_TEXT_MODEL,
    DEFAULT_GEMINI_VIDEO_MODEL,
    resolve_gemini_model_for_modality,
)


def test_resolve_gemini_modality_slots():
    cfg = {
        "text_model": "gemini-2.5-pro",
        "image_model": "gemini-3.1-flash-image-preview",
        "video_model": "veo-3.1-generate-preview",
        "audio_model": "lyria-3.5",
    }
    assert resolve_gemini_model_for_modality(cfg, "text") == "gemini-2.5-pro"
    assert (
        resolve_gemini_model_for_modality(cfg, "image")
        == "gemini-3.1-flash-image-preview"
    )
    assert resolve_gemini_model_for_modality(cfg, "video") == "veo-3.1-generate-preview"
    assert resolve_gemini_model_for_modality(cfg, "audio") == "lyria-3.5"


def test_resolve_gemini_defaults_when_empty():
    assert resolve_gemini_model_for_modality({}, "text") == DEFAULT_GEMINI_TEXT_MODEL
    assert resolve_gemini_model_for_modality({}, "image") == DEFAULT_GEMINI_IMAGE_MODEL
    assert resolve_gemini_model_for_modality({}, "video") == DEFAULT_GEMINI_VIDEO_MODEL
    assert resolve_gemini_model_for_modality({}, "audio") == DEFAULT_GEMINI_AUDIO_MODEL


def test_resolve_gemini_remaps_retired_text_model():
    cfg = {"text_model": "gemini-2.0-flash-lite"}
    assert resolve_gemini_model_for_modality(cfg, "text") == "gemini-3.1-flash-lite"
    cfg2 = {"text_model": "gemini-2.5-flash-lite"}
    assert resolve_gemini_model_for_modality(cfg2, "text") == "gemini-3.1-flash-lite"
