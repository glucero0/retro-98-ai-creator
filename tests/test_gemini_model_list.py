"""Gemini live model listing helpers + modality classification."""

from retro_98_ai_creator.gemini_provider import (
    _gemini_model_id,
    _gemini_model_label,
    _gemini_model_notes,
    _is_studio_gemini_model,
    _is_text_generation_gemini_model,
)
from retro_98_ai_creator.modality import classify_model_modality


def test_gemini_model_id_strips_prefix():
    assert _gemini_model_id("models/gemini-2.5-flash") == "gemini-2.5-flash"
    assert _gemini_model_id("gemini-2.5-pro") == "gemini-2.5-pro"


def test_gemini_model_label_and_notes():
    assert "Flash" in _gemini_model_label("gemini-2.5-flash", None)
    assert "recommended" in _gemini_model_notes("gemini-2.5-flash").lower()
    assert "quality" in _gemini_model_notes("gemini-2.5-pro").lower()


def test_keeps_text_gemini_models():
    for mid in (
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
    ):
        assert _is_text_generation_gemini_model(mid, supported_actions=["generateContent"])
        assert classify_model_modality(mid) == "text"


def test_retired_gemini_2_0_models_are_hidden():
    for mid in (
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "models/gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite",
    ):
        assert not _is_studio_gemini_model(mid, supported_actions=["generateContent"])


def test_normalize_remaps_retired_gemini_models():
    from retro_98_ai_creator.gemini_provider import normalize_gemini_model

    assert normalize_gemini_model("gemini-2.0-flash-lite") == "gemini-3.1-flash-lite"
    assert (
        normalize_gemini_model("models/gemini-2.0-flash-lite") == "gemini-3.1-flash-lite"
    )
    assert normalize_gemini_model("gemini-2.5-flash-lite") == "gemini-3.1-flash-lite"
    assert normalize_gemini_model("gemini-2.0-flash") == "gemini-2.5-flash"
    assert normalize_gemini_model("gemini-2.5-flash") == "gemini-2.5-flash"


def test_classifies_image_and_video_models():
    image_ids = (
        "gemini-2.5-flash-image",
        "gemini-2.5-flash-preview-image-generation",
        "gemini-3.1-flash-image-preview",
        "imagen-3.0-generate-002",
    )
    for mid in image_ids:
        assert classify_model_modality(mid) == "image"
        assert _is_studio_gemini_model(mid)
        assert not _is_text_generation_gemini_model(mid)

    # Retired 2.0 image preview is remapped / hidden from the picker
    assert (
        classify_model_modality("gemini-2.0-flash-preview-image-generation") == "image"
    )
    assert not _is_studio_gemini_model("gemini-2.0-flash-preview-image-generation")

    for mid in (
        "veo-2.0-generate-001",
        "veo-3.1-generate-preview",
        "veo-3.1-fast-generate-preview",
    ):
        assert classify_model_modality(mid) == "video"
        assert _is_studio_gemini_model(mid)
        assert not _is_text_generation_gemini_model(mid)


def test_skips_audio_live_tts_embedding():
    for mid in (
        "gemini-2.5-flash-preview-tts",
        "gemini-2.5-flash-native-audio-preview",
        "gemini-2.0-flash-live-001",
        "gemini-embedding-001",
        "gemini-robotics-er-1.5-preview",
    ):
        assert not _is_studio_gemini_model(mid)
        assert classify_model_modality(mid) is None or not _is_text_generation_gemini_model(mid)


def test_skips_media_by_description_not_video_games():
    assert classify_model_modality(
        "gemini-2.5-flash-special",
        description="Model for image generation and creative art.",
    ) == "image"
    # Mentions of video games must not exclude text models
    assert _is_text_generation_gemini_model(
        "gemini-2.5-flash",
        description="Helpful for answering questions about video games.",
        supported_actions=["generateContent"],
    )
