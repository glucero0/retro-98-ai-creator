"""Gemini multi-slot model config (text / image / video)."""

from retro_98_ai_creator.gemini_provider import (
    DEFAULT_GEMINI_IMAGE_MODEL,
    DEFAULT_GEMINI_TEXT_MODEL,
    DEFAULT_GEMINI_VIDEO_MODEL,
    migrate_gemini_model_config,
    resolve_gemini_model_for_modality,
)


def test_migrate_legacy_text_model():
    cfg = migrate_gemini_model_config({"model": "gemini-2.5-flash"})
    assert cfg["text_model"] == "gemini-2.5-flash"
    assert cfg["image_model"] == DEFAULT_GEMINI_IMAGE_MODEL
    assert cfg["video_model"] == DEFAULT_GEMINI_VIDEO_MODEL
    assert cfg["model"] == cfg["text_model"]


def test_migrate_legacy_image_model():
    cfg = migrate_gemini_model_config({"model": "gemini-2.5-flash-image"})
    assert cfg["image_model"] == "gemini-2.5-flash-image"
    assert cfg["text_model"] == DEFAULT_GEMINI_TEXT_MODEL
    assert cfg["video_model"] == DEFAULT_GEMINI_VIDEO_MODEL


def test_resolve_modality_slots():
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
