"""OpenRouter image generation with a Studio media basis."""

from __future__ import annotations

import base64
from unittest.mock import patch

import pytest

from retro_98_ai_creator.openrouter_media import (
    _extract_chat_image_bytes,
    generate_image_with_openrouter,
)


def test_extract_chat_image_bytes_from_message_images():
    png = base64.b64encode(b"fakepng").decode("ascii")
    body = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Here you go",
                    "images": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{png}"},
                        }
                    ],
                }
            }
        ]
    }
    data, mime = _extract_chat_image_bytes(body)
    assert data == b"fakepng"
    assert mime == "image/png"


def test_generate_image_with_basis_uses_input_references_then_chat_fallback():
    png = base64.b64encode(b"outimg").decode("ascii")
    calls: list[dict] = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        url = kwargs.get("url") or ""
        if url.endswith("/images"):
            raise RuntimeError(
                'OpenRouter HTTP 400: {"error":{"message":'
                '"Gemini returned no image data (finish_reason: STOP)"}}'
            )
        if url.endswith("/chat/completions"):
            return {
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": f"data:image/png;base64,{png}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        raise AssertionError(f"unexpected url {url}")

    cfg = {
        "api_key": "test-key",
        "image_model": "google/gemini-2.5-flash-image",
        "base_url": "https://openrouter.ai/api/v1",
    }
    basis = {"bytes": b"basisimg", "mime_type": "image/png", "modality": "image"}

    with (
        patch(
            "retro_98_ai_creator.openrouter_media._request_json",
            side_effect=fake_request,
        ),
        patch(
            "retro_98_ai_creator.openrouter_media.write_media_bytes",
            return_value={"mediaPath": "media/doc_x.png", "mimeType": "image/png"},
        ),
    ):
        creation = generate_image_with_openrouter(
            "make it rainy",
            openrouter_cfg=cfg,
            basis_media=basis,
        )

    assert creation["modality"] == "image"
    assert len(calls) == 2
    images_payload = calls[0]["payload"]
    assert "input_references" in images_payload
    assert images_payload["input_references"][0]["type"] == "image_url"
    assert "image" not in images_payload
    chat_payload = calls[1]["payload"]
    assert chat_payload["modalities"] == ["image", "text"]
    assert isinstance(chat_payload["messages"][0]["content"], list)


def test_generate_image_with_basis_raises_when_both_paths_fail():
    def fake_request(**kwargs):
        raise RuntimeError("OpenRouter HTTP 400: boom")

    cfg = {
        "api_key": "test-key",
        "image_model": "google/gemini-2.5-flash-image",
    }
    with patch(
        "retro_98_ai_creator.openrouter_media._request_json",
        side_effect=fake_request,
    ):
        with pytest.raises(RuntimeError, match="with basis"):
            generate_image_with_openrouter(
                "make it rainy",
                openrouter_cfg=cfg,
                basis_media={"bytes": b"x", "mime_type": "image/png"},
            )


def test_generate_video_with_basis_sends_frame_images():
    from retro_98_ai_creator.openrouter_media import generate_video_with_openrouter

    calls: list[dict] = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        url = kwargs.get("url") or ""
        if url.endswith("/videos") and kwargs.get("method") == "POST":
            return {
                "id": "job_1",
                "polling_url": "https://openrouter.ai/api/v1/videos/job_1",
                "status": "pending",
            }
        if "/videos/job_1" in url and kwargs.get("method") == "GET":
            return {"status": "completed", "id": "job_1", "unsigned_urls": []}
        raise AssertionError(f"unexpected {kwargs}")

    cfg = {
        "api_key": "test-key",
        "video_model": "google/veo-3.1",
        "base_url": "https://openrouter.ai/api/v1",
    }
    with (
        patch(
            "retro_98_ai_creator.openrouter_media._request_json",
            side_effect=fake_request,
        ),
        patch(
            "retro_98_ai_creator.openrouter_media._download_bytes",
            return_value=b"fake-mp4",
        ),
        patch(
            "retro_98_ai_creator.openrouter_media.write_media_bytes",
            return_value={"mediaPath": "media/doc_v.mp4", "mimeType": "video/mp4"},
        ),
        patch("retro_98_ai_creator.openrouter_media.time.sleep", return_value=None),
    ):
        creation = generate_video_with_openrouter(
            "turn this into a video of the subject waving",
            openrouter_cfg=cfg,
            basis_media={"bytes": b"basis", "mime_type": "image/png"},
        )

    assert creation["modality"] == "video"
    submit = calls[0]["payload"]
    assert "frame_images" in submit
    assert submit["frame_images"][0]["frame_type"] == "first_frame"
    assert "image" not in submit
