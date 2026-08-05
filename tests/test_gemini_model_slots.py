"""Gemini / OpenRouter / Hugging Face modality model resolution."""

from retro_98_ai_creator.config import (
    DEFAULT_HF_IMAGE_MODEL,
    DEFAULT_HF_TEXT_MODEL,
    DEFAULT_HF_VIDEO_MODEL,
)
from retro_98_ai_creator.gemini_provider import (
    DEFAULT_GEMINI_IMAGE_MODEL,
    DEFAULT_GEMINI_TEXT_MODEL,
    DEFAULT_GEMINI_VIDEO_MODEL,
    resolve_gemini_model_for_modality,
)
from retro_98_ai_creator.hf_provider import resolve_hf_model_for_modality
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


def test_resolve_gemini_remaps_retired_text_model():
    cfg = {"text_model": "gemini-2.0-flash-lite"}
    assert resolve_gemini_model_for_modality(cfg, "text") == "gemini-3.1-flash-lite"
    cfg2 = {"text_model": "gemini-2.5-flash-lite"}
    assert resolve_gemini_model_for_modality(cfg2, "text") == "gemini-3.1-flash-lite"


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


def test_resolve_hf_modality_slots():
    cfg = {
        "text_model": "Qwen/Qwen2.5-3B-Instruct",
        "image_model": "stabilityai/sd-turbo",
        "video_model": "cerspense/zeroscope_v2_576w",
    }
    assert resolve_hf_model_for_modality(cfg, "text") == "Qwen/Qwen2.5-3B-Instruct"
    assert resolve_hf_model_for_modality(cfg, "image") == "stabilityai/sd-turbo"
    assert (
        resolve_hf_model_for_modality(cfg, "video") == "cerspense/zeroscope_v2_576w"
    )


def test_resolve_hf_defaults_and_repo_id_alias():
    assert resolve_hf_model_for_modality({}, "text") == DEFAULT_HF_TEXT_MODEL
    assert resolve_hf_model_for_modality({}, "image") == DEFAULT_HF_IMAGE_MODEL
    assert resolve_hf_model_for_modality({}, "video") == DEFAULT_HF_VIDEO_MODEL
    # Older configs only had repo_id for text
    assert (
        resolve_hf_model_for_modality(
            {"repo_id": "google/gemma-2-2b-it"}, "text"
        )
        == "google/gemma-2-2b-it"
    )
