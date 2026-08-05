"""Hugging Face Studio media-basis (img2img / video-from-basis) wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from retro_98_ai_creator.hf_media import (
    _basis_to_pil,
    _repo_likely_supports_i2v,
    generate_image_with_hf,
    generate_video_with_hf,
)

# Minimal 1x1 PNG
_MIN_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_repo_likely_supports_i2v():
    assert _repo_likely_supports_i2v("ali-vilab/text-to-video-ms-1.7b") is False
    assert _repo_likely_supports_i2v("stabilityai/stable-video-diffusion-img2vid-xt") is True
    assert _repo_likely_supports_i2v("some-org/wan-i2v-1.3b") is True


def test_basis_to_pil_roundtrip():
    pytest.importorskip("PIL")
    img = _basis_to_pil({"bytes": _MIN_PNG, "modality": "image", "mime_type": "image/png"})
    assert img is not None
    assert img.mode == "RGB"
    assert _basis_to_pil(None) is None
    assert _basis_to_pil({"bytes": b""}) is None


def test_generate_image_with_hf_uses_img2img_when_basis():
    fake_pil = MagicMock(name="basis_pil")
    out_img = MagicMock(name="out_img")
    fake_result = MagicMock()
    fake_result.images = [out_img]
    t2i = MagicMock(name="t2i")
    img2img = MagicMock(name="img2img", return_value=fake_result)

    fake_torch = MagicMock()
    fake_torch.inference_mode.return_value.__enter__ = MagicMock(return_value=None)
    fake_torch.inference_mode.return_value.__exit__ = MagicMock(return_value=False)

    with (
        patch.dict("sys.modules", {"torch": fake_torch}),
        patch(
            "retro_98_ai_creator.hf_media._basis_to_pil",
            return_value=fake_pil,
        ),
        patch(
            "retro_98_ai_creator.hf_media.local_media_manager.ensure_pipeline",
            return_value=t2i,
        ),
        patch(
            "retro_98_ai_creator.hf_media._as_img2img_pipeline",
            return_value=img2img,
        ),
        patch(
            "retro_98_ai_creator.hf_media._pil_to_png_bytes",
            return_value=b"png-bytes",
        ),
        patch(
            "retro_98_ai_creator.hf_media.write_media_bytes",
            return_value={"mediaPath": "media/x.png", "mimeType": "image/png"},
        ),
    ):
        creation = generate_image_with_hf(
            "make it rainy",
            model_cfg={"image_model": "stable-diffusion-v1-5/stable-diffusion-v1-5"},
            basis_media={
                "bytes": _MIN_PNG,
                "modality": "image",
                "mime_type": "image/png",
            },
        )

    assert creation["modality"] == "image"
    assert creation["_model"]["basis"] is True
    assert img2img.called
    kwargs = img2img.call_args.kwargs
    assert kwargs["image"] is fake_pil
    assert "strength" in kwargs
    assert kwargs["prompt"] == "make it rainy"


def test_generate_video_with_hf_basis_morphs_without_loading_t2v():
    fake_pil = MagicMock(name="basis_pil")
    out_img = MagicMock(name="out_img")
    fake_result = MagicMock()
    fake_result.images = [out_img]
    img2img = MagicMock(return_value=fake_result)
    t2i = MagicMock()
    ensure = MagicMock(return_value=t2i)

    fake_torch = MagicMock()
    fake_torch.inference_mode.return_value.__enter__ = MagicMock(return_value=None)
    fake_torch.inference_mode.return_value.__exit__ = MagicMock(return_value=False)
    fake_torch.Generator.return_value.manual_seed.return_value = MagicMock()

    with (
        patch.dict("sys.modules", {"torch": fake_torch}),
        patch(
            "retro_98_ai_creator.hf_media._basis_to_pil",
            return_value=fake_pil,
        ),
        patch(
            "retro_98_ai_creator.hf_media.local_media_manager.ensure_pipeline",
            ensure,
        ),
        patch(
            "retro_98_ai_creator.hf_media._as_img2img_pipeline",
            return_value=img2img,
        ),
        patch(
            "retro_98_ai_creator.hf_media._frames_to_mp4_bytes",
            return_value=b"\x00\x00\x00\x18ftypmp42",
        ),
        patch(
            "retro_98_ai_creator.hf_media.write_media_bytes",
            return_value={"mediaPath": "media/x.mp4", "mimeType": "video/mp4"},
        ),
    ):
        creation = generate_video_with_hf(
            "camera slowly pans",
            model_cfg={
                "image_model": "stable-diffusion-v1-5/stable-diffusion-v1-5",
                "video_model": "ali-vilab/text-to-video-ms-1.7b",
                "video_num_frames": 3,
            },
            basis_media={
                "bytes": _MIN_PNG,
                "modality": "video",
                "mime_type": "image/png",
            },
        )

    assert creation["modality"] == "video"
    assert creation["_model"]["basis"] is True
    assert creation["_model"]["basis_mode"] == "img2img_morph"
    assert ensure.call_count >= 1
    for call in ensure.call_args_list:
        assert call.kwargs.get("kind") == "image"
        assert "text-to-video" not in (call.kwargs.get("repo_id") or "")
    assert img2img.call_count == 3


def test_generator_passes_basis_to_huggingface():
    from retro_98_ai_creator.generator import generate_creation

    captured: dict = {}

    def fake_hf(*_a, **kwargs):
        captured.update(kwargs)
        return {"id": "doc_test", "modality": "image"}

    cfg = {
        "backend": {"provider": "huggingface"},
        "huggingface": {
            "text_model": "microsoft/Phi-3.5-mini-instruct",
            "image_model": "stable-diffusion-v1-5/stable-diffusion-v1-5",
            "video_model": "ali-vilab/text-to-video-ms-1.7b",
        },
        "prompt": {},
    }
    basis = {"bytes": b"abc", "modality": "image", "mime_type": "image/png"}

    with (
        patch(
            "retro_98_ai_creator.hf_provider.generate_with_huggingface",
            side_effect=fake_hf,
        ),
        patch(
            "retro_98_ai_creator.modality.check_prompt_model_compatibility",
            return_value={"ok": True},
        ),
    ):
        out = generate_creation(
            "Prompt",
            "General",
            "Custom",
            cfg,
            creation_description="turn it blue",
            basis_media=basis,
        )

    assert out["id"] == "doc_test"
    assert captured.get("basis_media") is basis
    assert captured.get("forced_modality") == "image"
