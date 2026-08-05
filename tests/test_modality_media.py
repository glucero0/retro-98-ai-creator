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
    resolve_generation_modality,
)


def test_normalize_and_classify():
    assert normalize_modality("IMAGE") == "image"
    assert classify_model_modality("gemini-2.5-flash") == "text"
    assert classify_model_modality("gemini-flash-latest") == "text"
    assert classify_model_modality("gemini-2.5-flash-image") == "image"
    assert classify_model_modality("google/gemini-2.5-flash-image") == "image"
    assert classify_model_modality("black-forest-labs/flux.2-pro") == "image"
    assert classify_model_modality("veo-3.1-generate-preview") == "video"
    assert classify_model_modality("google/veo-2.0") == "video"
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


def test_resolve_generation_modality_prompt_wins_over_image_basis():
    # Image basis + video prompt → I2V (video), not forced img2img
    assert (
        resolve_generation_modality(
            "Generate a video of the dragon standing up",
            basis_modality="image",
        )
        == "video"
    )
    assert (
        resolve_generation_modality(
            "turn this into a video",
            basis_modality="image",
        )
        == "video"
    )
    assert (
        resolve_generation_modality(
            "convert the image to a video clip",
            basis_modality="image",
        )
        == "video"
    )
    assert (
        resolve_generation_modality("make it blue", basis_modality="image") == "image"
    )
    assert (
        resolve_generation_modality("Create an image of a cat", basis_modality="video")
        == "image"
    )
    assert resolve_generation_modality("hello world") is None


def test_gemini_routes_image_prompt_ok():
    prompt = "create an image of a dragon in a suit"
    ok = check_prompt_model_compatibility(prompt, "gemini-flash-latest", provider="gemini")
    assert ok["ok"] is True
    assert ok.get("routed") is True
    assert ok["modelModality"] == "image"
    assert "flash-image" in ok["model"] or "image" in ok["model"]


def test_openrouter_routes_image_prompt_ok():
    prompt = "create an image of a dragon in a suit"
    ok = check_prompt_model_compatibility(
        prompt, "google/gemini-2.5-flash", provider="openrouter"
    )
    assert ok["ok"] is True
    assert ok.get("routed") is True
    assert ok["modelModality"] == "image"
    assert "image" in ok["model"] or "flux" in ok["model"]


def test_huggingface_routes_image_and_video_prompts():
    image = check_prompt_model_compatibility(
        "create an image of a dragon in a suit",
        "microsoft/Phi-3.5-mini-instruct",
        provider="huggingface",
    )
    assert image["ok"] is True
    assert image.get("routed") is True
    assert image["modelModality"] == "image"
    assert "diffusion" in image["model"] or "sd" in image["model"].lower()

    video = check_prompt_model_compatibility(
        "Generate a video of waves",
        "microsoft/Phi-3.5-mini-instruct",
        provider="huggingface",
    )
    assert video["ok"] is True
    assert video.get("routed") is True
    assert video["modelModality"] == "video"
    assert "video" in video["model"].lower() or "zeroscope" in video["model"].lower()


def test_classify_local_diffusion_and_t2v():
    assert (
        classify_model_modality("stable-diffusion-v1-5/stable-diffusion-v1-5")
        == "image"
    )
    assert classify_model_modality("stabilityai/sd-turbo") == "image"
    assert classify_model_modality("ali-vilab/text-to-video-ms-1.7b") == "video"
    assert classify_model_modality("cerspense/zeroscope_v2_576w") == "video"


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
