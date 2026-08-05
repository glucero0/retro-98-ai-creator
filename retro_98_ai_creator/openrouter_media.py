"""OpenRouter image and video generation helpers."""

from __future__ import annotations

import base64
import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable
from urllib.parse import urljoin

from .creation_utils import build_media_creation, title_from_prompt
from .media_store import write_media_bytes
from .modality import classify_model_modality

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]


def _emit(
    progress: ProgressCallback | None,
    message: str,
    *,
    percent: float | None = None,
    title: str = "Generating",
) -> None:
    if not progress:
        return
    from .cancellation import GenerationCancelled

    payload: dict[str, Any] = {
        "message": message,
        "phase": "generate",
        "title": title,
    }
    if percent is not None:
        payload["percent"] = percent
    try:
        progress(payload)
    except GenerationCancelled:
        raise
    except Exception:  # noqa: BLE001
        logger.debug("progress callback failed", exc_info=True)


def _request_json(
    *,
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 180,
    cancel_event: Any = None,
) -> Any:
    from .cancellation import run_cancellable

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": "Retro 98 AI Creator",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    def _do() -> Any:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter network error: {exc.reason}") from exc

    return run_cancellable(_do, cancel_event)


def _download_bytes(
    url: str, *, api_key: str, timeout: float = 180, cancel_event: Any = None
) -> bytes:
    from .cancellation import run_cancellable

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Title": "Retro 98 AI Creator",
        },
    )

    def _do() -> bytes:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise RuntimeError(f"OpenRouter download HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter download error: {exc.reason}") from exc

    return run_cancellable(_do, cancel_event)


def _decode_data_url(url: str) -> tuple[bytes, str] | None:
    raw = (url or "").strip()
    if not raw.startswith("data:") or ";base64," not in raw:
        return None
    header, b64 = raw.split(";base64,", 1)
    mime = header[5:] or "image/png"
    try:
        return base64.b64decode(b64), mime
    except Exception:  # noqa: BLE001
        return None


def _extract_images_api_bytes(body: Any) -> tuple[bytes | None, str]:
    image_bytes: bytes | None = None
    mime_type = "image/png"
    if not isinstance(body, dict):
        return None, mime_type
    for item in body.get("data") or []:
        if not isinstance(item, dict):
            continue
        b64 = item.get("b64_json") or item.get("b64")
        if b64:
            image_bytes = base64.b64decode(b64)
            mime_type = str(item.get("media_type") or mime_type)
            break
        img_url = item.get("url")
        if img_url and str(img_url).startswith("data:"):
            decoded = _decode_data_url(str(img_url))
            if decoded:
                image_bytes, mime_type = decoded
                break
    return image_bytes, mime_type


def _extract_chat_image_bytes(body: Any) -> tuple[bytes | None, str]:
    """Parse OpenRouter chat/completions image output (message.images)."""
    mime_type = "image/png"
    if not isinstance(body, dict):
        return None, mime_type
    choices = body.get("choices") or []
    if not choices:
        return None, mime_type
    message = (choices[0] or {}).get("message") or {}
    images = message.get("images") or []
    for image in images:
        if not isinstance(image, dict):
            continue
        img = image.get("image_url") or image.get("imageUrl") or {}
        url = ""
        if isinstance(img, dict):
            url = str(img.get("url") or "")
        elif isinstance(img, str):
            url = img
        decoded = _decode_data_url(url)
        if decoded:
            return decoded
    # Some providers put a lone data URL in content
    content = message.get("content")
    if isinstance(content, str) and content.startswith("data:image"):
        decoded = _decode_data_url(content)
        if decoded:
            return decoded
    return None, mime_type


def generate_image_with_openrouter(
    prompt: str,
    *,
    openrouter_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    basis_media: dict[str, Any] | None = None,
    cancel_event: Any = None,
) -> dict[str, Any]:
    """Generate an image via OpenRouter ``POST /images`` (or chat modalities fallback)."""
    from .openrouter_provider import (
        DEFAULT_OPENROUTER_IMAGE_MODEL,
        OPENROUTER_BASE_URL,
        normalize_openrouter_model,
        resolve_api_key,
        resolve_openrouter_model_for_modality,
    )

    cfg = dict(openrouter_cfg or {})
    api_key = resolve_api_key(cfg)
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key missing. Paste your key in Control Panel → AI Model (OpenRouter)."
        )
    prompt = (prompt or "").strip()
    if not prompt:
        raise RuntimeError("Enter a prompt to generate an image.")

    model_name = resolve_openrouter_model_for_modality(cfg, "image")
    if (classify_model_modality(model_name) or "text") != "image":
        model_name = normalize_openrouter_model(DEFAULT_OPENROUTER_IMAGE_MODEL)

    base_url = (cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL
    images_url = base_url.rstrip("/") + "/images"
    chat_url = base_url.rstrip("/") + "/chat/completions"

    _emit(
        progress,
        f"Contacting OpenRouter image model ({model_name})…",
        percent=15,
        title="Generating image",
    )
    _emit(
        progress,
        "Generating image from basis…" if basis_media else "Generating image…",
        percent=40,
        title="Generating image",
    )

    basis_bytes = (basis_media or {}).get("bytes") if basis_media else None
    basis_mime = str((basis_media or {}).get("mime_type") or "image/png")
    data_url = ""
    edit_prompt = prompt
    if basis_bytes:
        b64 = base64.b64encode(bytes(basis_bytes)).decode("ascii")
        data_url = f"data:{basis_mime};base64,{b64}"
        edit_prompt = (
            "Using the provided reference image as the basis, create a new image. "
            "Follow this instruction:\n" + prompt
        )

    payload: dict[str, Any] = {"model": model_name, "prompt": edit_prompt, "n": 1}
    if data_url:
        # Official Images API field for image-to-image / edits
        payload["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url}}
        ]

    body: Any = None
    last_err: Exception | None = None
    try:
        body = _request_json(
            method="POST",
            url=images_url,
            api_key=api_key,
            payload=payload,
            timeout=300,
            cancel_event=cancel_event,
        )
    except Exception as exc:
        from .cancellation import GenerationCancelled

        if isinstance(exc, GenerationCancelled):
            raise
        last_err = exc
        logger.info("OpenRouter /images failed (%s); trying chat modalities", exc)

    image_bytes: bytes | None = None
    mime_type = "image/png"
    if body is not None:
        image_bytes, mime_type = _extract_images_api_bytes(body)
        if not image_bytes:
            for item in body.get("data") or []:
                if not isinstance(item, dict):
                    continue
                remote = item.get("url")
                if remote and not str(remote).startswith("data:"):
                    try:
                        image_bytes = _download_bytes(
                            str(remote),
                            api_key=api_key,
                            cancel_event=cancel_event,
                        )
                    except Exception as exc:  # noqa: BLE001
                        from .cancellation import GenerationCancelled

                        if isinstance(exc, GenerationCancelled):
                            raise
                        last_err = exc
                    break
        if not image_bytes:
            # Empty / unusable — often Gemini STOP with a bad reference field
            last_err = last_err or RuntimeError(
                f"OpenRouter returned no image data: {body!r}"
            )

    # Gemini (and some other multimodal image models) are more reliable via
    # chat/completions + modalities, especially with a reference image.
    if not image_bytes:
        chat_content: list[dict[str, Any]] | str
        if data_url:
            chat_content = [
                {"type": "text", "text": edit_prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
        else:
            chat_content = edit_prompt
        chat_payload: dict[str, Any] = {
            "model": model_name,
            "messages": [{"role": "user", "content": chat_content}],
            # Gemini image models expect both; pure image models accept ["image"]
            "modalities": ["image", "text"],
        }
        try:
            chat_body = _request_json(
                method="POST",
                url=chat_url,
                api_key=api_key,
                payload=chat_payload,
                timeout=300,
                cancel_event=cancel_event,
            )
            image_bytes, mime_type = _extract_chat_image_bytes(chat_body)
            if not image_bytes:
                raise RuntimeError(
                    f"OpenRouter chat image response had no images: {chat_body!r}"
                )
        except Exception as exc:
            from .cancellation import GenerationCancelled

            if isinstance(exc, GenerationCancelled):
                raise
            if last_err is not None:
                raise RuntimeError(
                    f"OpenRouter image generation error"
                    f"{' (with basis)' if basis_bytes else ''}: {last_err}; "
                    f"chat fallback: {exc}"
                ) from exc
            raise RuntimeError(
                f"OpenRouter image generation error"
                f"{' (with basis)' if basis_bytes else ''}: {exc}"
            ) from exc

    if not image_bytes:
        raise RuntimeError(
            f"OpenRouter image generation error"
            f"{' (with basis)' if basis_bytes else ''}: {last_err or 'no image data'}"
        )

    _emit(progress, "Saving image…", percent=85, title="Generating image")
    creation_id = f"doc_{uuid.uuid4().hex[:10]}"
    stored = write_media_bytes(creation_id, image_bytes, mime_type=mime_type)
    return build_media_creation(
        modality="image",
        prompt=prompt,
        media_path=stored["mediaPath"],
        mime_type=stored["mimeType"],
        title=title_from_prompt(prompt),
        model_info={
            "provider": "openrouter",
            "repo_id": model_name,
            "modality": "image",
            "basis": bool(basis_bytes),
        },
        creation_id=creation_id,
    )


def generate_video_with_openrouter(
    prompt: str,
    *,
    openrouter_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    basis_media: dict[str, Any] | None = None,
    cancel_event: Any = None,
) -> dict[str, Any]:
    """Generate a video via OpenRouter async ``/videos`` and store under media/."""
    from .openrouter_provider import (
        DEFAULT_OPENROUTER_VIDEO_MODEL,
        OPENROUTER_BASE_URL,
        normalize_openrouter_model,
        resolve_api_key,
        resolve_openrouter_model_for_modality,
    )

    cfg = dict(openrouter_cfg or {})
    api_key = resolve_api_key(cfg)
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key missing. Paste your key in Control Panel → AI Model (OpenRouter)."
        )
    prompt = (prompt or "").strip()
    if not prompt:
        raise RuntimeError("Enter a prompt to generate a video.")

    model_name = resolve_openrouter_model_for_modality(cfg, "video")
    if (classify_model_modality(model_name) or "text") != "video":
        model_name = normalize_openrouter_model(DEFAULT_OPENROUTER_VIDEO_MODEL)

    base_url = (cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL
    submit_url = base_url.rstrip("/") + "/videos"

    _emit(
        progress,
        f"Contacting OpenRouter video model ({model_name})…",
        percent=10,
        title="Generating video",
    )

    payload: dict[str, Any] = {"model": model_name, "prompt": prompt}
    basis_bytes = (basis_media or {}).get("bytes") if basis_media else None
    basis_mime = str((basis_media or {}).get("mime_type") or "image/png")
    data_url = ""
    if basis_bytes:
        b64 = base64.b64encode(bytes(basis_bytes)).decode("ascii")
        data_url = f"data:{basis_mime};base64,{b64}"
        # Official OpenRouter I2V field (not legacy "image")
        payload["frame_images"] = [
            {
                "type": "image_url",
                "image_url": {"url": data_url},
                "frame_type": "first_frame",
            }
        ]
        payload["prompt"] = (
            "Using the provided reference image as the starting frame / basis, "
            "generate a new video. Follow this instruction:\n" + prompt
        )

    try:
        job = _request_json(
            method="POST",
            url=submit_url,
            api_key=api_key,
            payload=payload,
            timeout=120,
            cancel_event=cancel_event,
        )
    except Exception as exc:
        from .cancellation import GenerationCancelled

        if isinstance(exc, GenerationCancelled):
            raise
        if basis_bytes and data_url:
            # Retry with input_references (style/guidance) if frame_images rejected
            try:
                logger.info(
                    "OpenRouter video frame_images rejected (%s); trying input_references",
                    exc,
                )
                job = _request_json(
                    method="POST",
                    url=submit_url,
                    api_key=api_key,
                    payload={
                        "model": model_name,
                        "prompt": payload["prompt"],
                        "input_references": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            }
                        ],
                    },
                    timeout=120,
                    cancel_event=cancel_event,
                )
            except Exception as exc2:
                from .cancellation import GenerationCancelled as _GC

                if isinstance(exc2, _GC):
                    raise
                raise RuntimeError(
                    f"OpenRouter video submit error (with basis): {exc2}"
                ) from exc2
        else:
            raise RuntimeError(f"OpenRouter video submit error: {exc}") from exc

    job_id = str(job.get("id") or "").strip()
    polling_url = str(job.get("polling_url") or "").strip()
    if not polling_url and job_id:
        polling_url = base_url.rstrip("/") + f"/videos/{job_id}"
    elif polling_url.startswith("/"):
        polling_url = urljoin(base_url, polling_url)
    if not polling_url:
        raise RuntimeError(f"OpenRouter video job missing polling URL: {job!r}")

    _emit(progress, "Waiting for video…", percent=25, title="Generating video")
    status_body: dict[str, Any] = {}
    waited = 0
    deadline = time.time() + 15 * 60
    while time.time() < deadline:
        # 1s ticks so Cancel is noticed quickly (progress raises GenerationCancelled).
        time.sleep(1)
        waited += 1
        pct = min(75, 25 + waited // 4)
        _emit(
            progress,
            f"Rendering video… ({waited}s)",
            percent=pct,
            title="Generating video",
        )
        if waited % 8 != 0 and waited > 1:
            continue
        try:
            status_body = _request_json(
                method="GET",
                url=polling_url,
                api_key=api_key,
                timeout=60,
                cancel_event=cancel_event,
            )
        except Exception as exc:
            from .cancellation import GenerationCancelled

            if isinstance(exc, GenerationCancelled):
                raise
            raise RuntimeError(f"OpenRouter video poll error: {exc}") from exc

        status = str(status_body.get("status") or "").lower()
        if status == "completed":
            break
        if status in {"failed", "cancelled", "expired"}:
            err = status_body.get("error") or status
            raise RuntimeError(f"OpenRouter video generation {status}: {err}")
    else:
        raise RuntimeError("OpenRouter video generation timed out.")

    urls = status_body.get("unsigned_urls") or []
    if not urls:
        content_path = f"/videos/{job_id or status_body.get('id')}/content"
        # Prefer absolute path under the OpenRouter host
        parsed_base = urljoin(base_url.rstrip("/") + "/", ".")
        urls = [urljoin(parsed_base, content_path)]

    content_url = str(urls[0])
    if content_url.startswith("/"):
        content_url = urljoin(base_url, content_url)

    _emit(progress, "Downloading video…", percent=80, title="Generating video")
    video_bytes = _download_bytes(
        content_url, api_key=api_key, timeout=300, cancel_event=cancel_event
    )
    if not video_bytes:
        raise RuntimeError("OpenRouter returned empty video content.")

    _emit(progress, "Saving video…", percent=90, title="Generating video")
    creation_id = f"doc_{uuid.uuid4().hex[:10]}"
    stored = write_media_bytes(creation_id, video_bytes, mime_type="video/mp4")
    return build_media_creation(
        modality="video",
        prompt=prompt,
        media_path=stored["mediaPath"],
        mime_type=stored["mimeType"],
        title=title_from_prompt(prompt),
        model_info={
            "provider": "openrouter",
            "repo_id": model_name,
            "modality": "video",
        },
        creation_id=creation_id,
    )
