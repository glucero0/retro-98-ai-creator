"""Modality helpers and media creation records."""

from pathlib import Path

from retro_98_ai_creator.creation_utils import (
    build_media_creation,
    build_text_creation_from_plain,
    is_generic_studio_request,
    title_from_prompt,
)
from retro_98_ai_creator.media_store import write_media_bytes
from retro_98_ai_creator.modality import (
    check_prompt_model_compatibility,
    classify_model_modality,
    infer_prompt_modality,
    normalize_modality,
)


def test_normalize_and_classify():
    assert normalize_modality("IMAGE") == "image"
    assert classify_model_modality("gemini-2.5-flash") == "text"
    assert classify_model_modality("gemini-flash-latest") == "text"
    assert classify_model_modality("gemini-2.5-flash-image") == "image"
    assert classify_model_modality("veo-3.1-generate-preview") == "video"
    assert classify_model_modality("gemini-2.5-flash-preview-tts") is None


def test_infer_prompt_modality_image_dragon():
    prompt = (
        "create an image of a dragon sitting in a lounge chair, smoking a pipe, "
        "reading the nyt -- it's wearing a suite, tie, and there's a stylish hat "
        "on the table next to him. the room has nice paintings, plants, and other "
        "adornments. very posh"
    )
    assert infer_prompt_modality(prompt) == "image"


def test_infer_prompt_modality_video_and_text():
    assert infer_prompt_modality("Generate a video of waves crashing") == "video"
    assert infer_prompt_modality("Write a short poem about autumn") == "text"
    assert infer_prompt_modality("a red bicycle leaning on a fence") is None


def test_gemini_routes_image_prompt_ok():
    prompt = "create an image of a dragon in a suit"
    ok = check_prompt_model_compatibility(prompt, "gemini-flash-latest", provider="gemini")
    assert ok["ok"] is True
    assert ok.get("routed") is True
    assert ok["modelModality"] == "image"
    assert "flash-image" in ok["model"] or "image" in ok["model"]


def test_openrouter_blocks_image_prompt():
    prompt = "create an image of a dragon in a suit"
    bad = check_prompt_model_compatibility(
        prompt, "google/gemini-2.5-flash", provider="openrouter"
    )
    assert bad["ok"] is False
    assert bad["promptModality"] == "image"
    assert "Gemini" in bad["error"]


def test_huggingface_blocks_video_prompt():
    bad = check_prompt_model_compatibility(
        "Generate a video of waves",
        "microsoft/Phi-3.5-mini-instruct",
        provider="huggingface",
    )
    assert bad["ok"] is False
    assert bad["promptModality"] == "video"


def test_generic_studio_request():
    assert is_generic_studio_request("Prompt", "General", "Custom")
    assert not is_generic_studio_request("Sonic", "Sega Genesis", "Quick Reference Card")


def test_title_from_prompt():
    assert title_from_prompt("Hello world\nmore") == "Hello world"
    assert title_from_prompt("") == "Untitled"


def test_build_text_and_media_creation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "retro_98_ai_creator.media_store.PROJECT_ROOT", tmp_path
    )
    monkeypatch.setattr(
        "retro_98_ai_creator.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )
    text = build_text_creation_from_plain(
        "Body text here", prompt="Write a poem", model_info={"provider": "test"}
    )
    assert text["modality"] == "text"
    assert text["prompt"] == "Write a poem"
    assert text["overview"] == ""
    assert "Body text" in text["sections"][0]["content"]
    assert text["sections"][0]["title"] == ""

    stored = write_media_bytes(
        "doc_abc123", b"\x89PNG\r\n", mime_type="image/png", config={"paths": {"media": "media"}}
    )
    assert stored["mediaPath"].endswith(".png")
    assert (tmp_path / stored["mediaPath"]).exists()

    media = build_media_creation(
        modality="image",
        prompt="A red robot",
        media_path=stored["mediaPath"],
        mime_type=stored["mimeType"],
        creation_id="doc_abc123",
    )
    assert media["modality"] == "image"
    assert media["mediaPath"] == stored["mediaPath"]
    assert media["id"] == "doc_abc123"
