"""Local Hugging Face image and video generation via Diffusers."""

from __future__ import annotations

import io
import logging
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from .config import DEFAULT_HF_IMAGE_MODEL, DEFAULT_HF_VIDEO_MODEL, normalize_huggingface_cfg
from .creation_utils import build_media_creation, title_from_prompt
from .media_store import write_media_bytes

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

_MISSING_LOCAL = (
    "Local image/video generation requires optional deps. Run:\n"
    "  pip install -r requirements-local.txt"
)


def _emit(
    progress: ProgressCallback | None,
    message: str,
    *,
    percent: float | None = None,
    title: str = "Generating",
    phase: str = "generate",
) -> None:
    if not progress:
        return
    from .cancellation import GenerationCancelled

    payload: dict[str, Any] = {
        "message": message,
        "phase": phase,
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


def _raise_if_cancelled(cancel_event: Any) -> None:
    from .cancellation import raise_if_cancelled

    raise_if_cancelled(
        (lambda: bool(cancel_event is not None and cancel_event.is_set()))
        if cancel_event is not None
        else None
    )


def _resolve_dtype(name: str):
    import torch

    mapping = {
        "auto": "auto",
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    return mapping.get(str(name).lower(), "auto")


def _resolve_device(name: str) -> str:
    import torch

    name = (name or "auto").lower()
    if name != "auto":
        return name
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _torch_dtype_for_device(device: str, dtype_cfg: Any):
    import torch

    resolved = _resolve_dtype(dtype_cfg if isinstance(dtype_cfg, str) else "auto")
    if resolved != "auto":
        return resolved
    if device in {"cuda", "mps"}:
        return torch.float16
    return torch.float32


def _pil_to_png_bytes(image: Any) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _basis_to_pil(basis_media: dict[str, Any] | None) -> Any | None:
    """Decode Studio basis bytes to an RGB PIL image, or None."""
    if not basis_media:
        return None
    raw = basis_media.get("bytes")
    if not raw:
        return None
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(_MISSING_LOCAL) from exc
    img = Image.open(io.BytesIO(bytes(raw)))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    return img


def _as_img2img_pipeline(pipe: Any) -> Any:
    """Reuse loaded T2I weights as an image-to-image pipeline when possible."""
    try:
        from diffusers import AutoPipelineForImage2Image

        return AutoPipelineForImage2Image.from_pipe(pipe)
    except Exception:  # noqa: BLE001
        logger.debug("AutoPipelineForImage2Image.from_pipe failed; trying components", exc_info=True)
    try:
        from diffusers import StableDiffusionImg2ImgPipeline

        return StableDiffusionImg2ImgPipeline(**pipe.components)
    except Exception as exc:
        raise RuntimeError(
            "This local image model could not be converted to image-to-image "
            f"(Studio media basis). Try a Stable Diffusion style checkpoint. ({exc})"
        ) from exc


def _pipe_accepts_kwarg(pipe: Any, name: str) -> bool:
    try:
        import inspect

        return name in inspect.signature(pipe.__call__).parameters
    except Exception:  # noqa: BLE001
        return False


def _frames_to_mp4_bytes(frames: list[Any], *, fps: int = 8) -> bytes:
    """Encode a list of PIL images / ndarrays to MP4 bytes."""
    if not frames:
        raise RuntimeError("Video pipeline returned no frames.")

    try:
        from diffusers.utils import export_to_video
    except ImportError as exc:
        raise RuntimeError(_MISSING_LOCAL) from exc

    with tempfile.TemporaryDirectory(prefix="rgc_vid_") as tmp:
        out_path = Path(tmp) / "out.mp4"
        export_to_video(frames, str(out_path), fps=fps)
        data = out_path.read_bytes()
    if not data:
        raise RuntimeError("Failed to encode local video to MP4.")
    return data


def _is_turbo_repo(repo_id: str) -> bool:
    return "turbo" in (repo_id or "").lower()


def _repo_likely_supports_i2v(repo_id: str) -> bool:
    """Heuristic: only load the video slot for basis when the repo looks like I2V."""
    rid = (repo_id or "").lower()
    tokens = (
        "img2vid",
        "image-to-video",
        "i2v",
        "svd",
        "stable-video",
        "wan-i2v",
        "cogvideox-i2v",
        "hunyuan-video-i2v",
    )
    return any(t in rid for t in tokens)


class LocalMediaManager:
    """Loads Diffusers text-to-image / text-to-video pipelines (one at a time)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pipe: Any = None
        self._loaded_repo: str | None = None
        self._loaded_kind: str | None = None  # "image" | "video"
        self._device: str = "cpu"
        self._status = "idle"
        self._status_detail = "No local media pipeline loaded."

    @property
    def status(self) -> dict[str, Any]:
        return {
            "state": self._status,
            "detail": self._status_detail,
            "loaded_repo": self._loaded_repo,
            "loaded_kind": self._loaded_kind,
            "device": self._device,
        }

    def unload(self) -> None:
        with self._lock:
            self._pipe = None
            self._loaded_repo = None
            self._loaded_kind = None
            self._status = "idle"
            self._status_detail = "Local media pipeline unloaded."
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass

    def _unload_text_model(self) -> None:
        try:
            from .llm import model_manager

            model_manager.unload()
        except Exception:  # noqa: BLE001
            logger.debug("Could not unload text model before media load", exc_info=True)

    def ensure_pipeline(
        self,
        *,
        kind: str,
        repo_id: str,
        model_cfg: dict[str, Any],
        progress: ProgressCallback | None = None,
        cancel_event: Any = None,
    ) -> Any:
        kind = "video" if kind == "video" else "image"
        revision = (model_cfg.get("revision") or "main") or "main"
        token = model_cfg.get("hf_token") or None

        with self._lock:
            if (
                self._pipe is not None
                and self._loaded_repo == repo_id
                and self._loaded_kind == kind
            ):
                return self._pipe

            self._unload_text_model()
            if self._pipe is not None:
                self._pipe = None
                self._loaded_repo = None
                self._loaded_kind = None
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:  # noqa: BLE001
                    pass

            _raise_if_cancelled(cancel_event)
            self._status = "loading"
            self._status_detail = f"Downloading / loading {repo_id}…"
            _emit(
                progress,
                f"Downloading / loading {repo_id} from Hugging Face…",
                percent=5,
                title=f"Loading {kind} model",
                phase="download",
            )

            try:
                import torch
                from diffusers import DiffusionPipeline
            except ImportError as exc:
                raise RuntimeError(_MISSING_LOCAL) from exc

            # Reuse text-model download progress hooks when available
            restore_hooks: Callable[[], None] | None = None
            try:
                from .llm import _install_download_progress_hooks

                def _hook_emit(message: str, percent: float | None = None, **kwargs: Any) -> None:
                    self._status_detail = message
                    _emit(
                        progress,
                        message,
                        percent=percent,
                        title=kwargs.get("title") or f"Loading {kind} model",
                        phase=kwargs.get("phase") or "download",
                    )

                restore_hooks = _install_download_progress_hooks(_hook_emit)
            except Exception:  # noqa: BLE001
                restore_hooks = None

            device = _resolve_device(model_cfg.get("device", "auto"))
            dtype = _torch_dtype_for_device(device, model_cfg.get("torch_dtype", "auto"))

            load_kwargs: dict[str, Any] = {
                "torch_dtype": dtype,
                "revision": revision,
                "token": token,
            }

            try:
                _emit(
                    progress,
                    f"Loading {kind} pipeline weights for {repo_id}…",
                    percent=25,
                    title=f"Loading {kind} model",
                    phase="load",
                )
                pipe = DiffusionPipeline.from_pretrained(repo_id, **load_kwargs)
            except Exception as first_exc:
                # Retry with float32 on CPU-only hosts when fp16 load fails
                try:
                    import torch as _torch

                    if device == "cpu" and dtype != _torch.float32:
                        pipe = DiffusionPipeline.from_pretrained(
                            repo_id,
                            torch_dtype=_torch.float32,
                            revision=revision,
                            token=token,
                        )
                    else:
                        raise first_exc
                except Exception as exc:
                    self._status = "error"
                    self._status_detail = str(exc)
                    raise RuntimeError(
                        f"Failed to load local {kind} model {repo_id}: {exc}"
                    ) from exc
            finally:
                if restore_hooks:
                    try:
                        restore_hooks()
                    except Exception:  # noqa: BLE001
                        pass

            _raise_if_cancelled(cancel_event)
            _emit(
                progress,
                f"Moving {kind} pipeline to {device}…",
                percent=55,
                title=f"Loading {kind} model",
                phase="load",
            )
            try:
                pipe = pipe.to(device)
            except Exception as exc:
                raise RuntimeError(
                    f"Loaded {repo_id} but could not move it to {device}: {exc}"
                ) from exc

            # Memory helpers when available
            try:
                if hasattr(pipe, "enable_attention_slicing"):
                    pipe.enable_attention_slicing()
            except Exception:  # noqa: BLE001
                pass

            self._pipe = pipe
            self._loaded_repo = repo_id
            self._loaded_kind = kind
            self._device = device
            self._status = "ready"
            self._status_detail = f"Ready: {repo_id} ({kind}) on {device}"
            _emit(
                progress,
                self._status_detail,
                percent=70,
                title=f"{kind.capitalize()} model ready",
                phase="ready",
            )
            return self._pipe


local_media_manager = LocalMediaManager()


def generate_image_with_hf(
    prompt: str,
    *,
    model_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
    basis_media: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an image with a local Diffusers pipeline (T2I or img2img with basis)."""
    cfg = normalize_huggingface_cfg(model_cfg)
    prompt = (prompt or "").strip()
    if not prompt:
        raise RuntimeError("Enter a prompt to generate an image.")

    repo_id = (cfg.get("image_model") or DEFAULT_HF_IMAGE_MODEL).strip()
    init_image = _basis_to_pil(basis_media)
    _raise_if_cancelled(cancel_event)

    pipe = local_media_manager.ensure_pipeline(
        kind="image",
        repo_id=repo_id,
        model_cfg=cfg,
        progress=progress,
        cancel_event=cancel_event,
    )

    using_basis = init_image is not None
    if using_basis:
        _emit(
            progress,
            "Generating image from basis (img2img)…",
            percent=75,
            title="Generating image",
        )
        run_pipe = _as_img2img_pipeline(pipe)
    else:
        _emit(progress, "Generating image…", percent=75, title="Generating image")
        run_pipe = pipe

    _raise_if_cancelled(cancel_event)

    steps = 4 if _is_turbo_repo(repo_id) else 28
    strength = float(cfg.get("img2img_strength") or 0.72)
    strength = max(0.15, min(0.95, strength))
    gen_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "num_inference_steps": steps,
    }
    if _is_turbo_repo(repo_id):
        gen_kwargs["guidance_scale"] = 0.0
    if using_basis:
        # Keep basis detail readable; clamp for turbo (few steps)
        if _is_turbo_repo(repo_id):
            strength = min(strength, 0.85)
        gen_kwargs["image"] = init_image
        gen_kwargs["strength"] = strength

    try:
        import torch

        with torch.inference_mode():
            result = run_pipe(**gen_kwargs)
        images = getattr(result, "images", None) or []
        if not images:
            raise RuntimeError("Local image pipeline returned no images.")
        image = images[0]
    except Exception as exc:
        from .cancellation import GenerationCancelled

        if isinstance(exc, GenerationCancelled):
            raise
        raise RuntimeError(f"Local image generation error: {exc}") from exc

    _raise_if_cancelled(cancel_event)
    _emit(progress, "Saving image…", percent=90, title="Generating image")
    image_bytes = _pil_to_png_bytes(image)
    creation_id = f"doc_{uuid.uuid4().hex[:10]}"
    stored = write_media_bytes(creation_id, image_bytes, mime_type="image/png")
    return build_media_creation(
        modality="image",
        prompt=prompt,
        media_path=stored["mediaPath"],
        mime_type=stored["mimeType"],
        title=title_from_prompt(prompt),
        model_info={
            "provider": "huggingface",
            "repo_id": repo_id,
            "modality": "image",
            "device": local_media_manager.status.get("device"),
            "basis": using_basis,
            "img2img_strength": strength if using_basis else None,
        },
        creation_id=creation_id,
    )


def _generate_video_frames_from_basis(
    prompt: str,
    init_image: Any,
    *,
    model_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
    num_frames: int = 16,
) -> tuple[list[Any], str]:
    """
    Image-to-video when the configured T2V pipeline has no ``image`` input:
    morph the basis frame with the image model (img2img) across seeds.
    """
    cfg = normalize_huggingface_cfg(model_cfg)
    repo_id = (cfg.get("image_model") or DEFAULT_HF_IMAGE_MODEL).strip()
    pipe = local_media_manager.ensure_pipeline(
        kind="image",
        repo_id=repo_id,
        model_cfg=cfg,
        progress=progress,
        cancel_event=cancel_event,
    )
    img2img = _as_img2img_pipeline(pipe)
    steps = 4 if _is_turbo_repo(repo_id) else 22
    base_strength = float(cfg.get("img2img_strength") or 0.55)
    base_strength = max(0.2, min(0.85, base_strength))

    import torch

    frames: list[Any] = []
    current = init_image
    for i in range(max(2, num_frames)):
        _raise_if_cancelled(cancel_event)
        pct = 75 + int(15 * (i / max(1, num_frames - 1)))
        _emit(
            progress,
            f"Animating from basis frame {i + 1}/{num_frames}…",
            percent=min(89, pct),
            title="Generating video",
        )
        # Slight strength ramp so motion drifts from the reference
        strength = min(0.9, base_strength + (0.2 * i / max(1, num_frames - 1)))
        gen_kwargs: dict[str, Any] = {
            "prompt": prompt,
            "image": current,
            "strength": strength,
            "num_inference_steps": steps,
            "generator": torch.Generator(device="cpu").manual_seed(1000 + i),
        }
        if _is_turbo_repo(repo_id):
            gen_kwargs["guidance_scale"] = 0.0
        with torch.inference_mode():
            result = img2img(**gen_kwargs)
        images = getattr(result, "images", None) or []
        if not images:
            raise RuntimeError("Local img2img returned no frames for video basis.")
        current = images[0]
        frames.append(current)
    return frames, repo_id


def generate_video_with_hf(
    prompt: str,
    *,
    model_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
    basis_media: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a short video (T2V, or I2V / basis morph when a Studio basis is set)."""
    cfg = normalize_huggingface_cfg(model_cfg)
    prompt = (prompt or "").strip()
    if not prompt:
        raise RuntimeError("Enter a prompt to generate a video.")

    repo_id = (cfg.get("video_model") or DEFAULT_HF_VIDEO_MODEL).strip()
    init_image = _basis_to_pil(basis_media)
    using_basis = init_image is not None
    _raise_if_cancelled(cancel_event)

    num_frames = int(cfg.get("video_num_frames") or 16)
    steps = int(cfg.get("video_inference_steps") or 25)
    fps = int(cfg.get("video_fps") or 8)
    basis_mode = "none"
    model_used = repo_id

    if using_basis:
        # Default T2V checkpoints (e.g. ModelScope) have no image input — skip
        # loading them and morph from the basis with the image model instead.
        use_native = _repo_likely_supports_i2v(repo_id)
        if use_native:
            pipe = local_media_manager.ensure_pipeline(
                kind="video",
                repo_id=repo_id,
                model_cfg=cfg,
                progress=progress,
                cancel_event=cancel_event,
            )
            if not (
                _pipe_accepts_kwarg(pipe, "image")
                or _pipe_accepts_kwarg(pipe, "input_image")
            ):
                use_native = False

        if use_native:
            _emit(
                progress,
                "Generating video from basis (image-to-video)…",
                percent=75,
                title="Generating video",
            )
            _raise_if_cancelled(cancel_event)
            image_key = "image" if _pipe_accepts_kwarg(pipe, "image") else "input_image"
            call_kwargs: dict[str, Any] = {
                "prompt": prompt,
                image_key: init_image,
                "num_inference_steps": steps,
            }
            if _pipe_accepts_kwarg(pipe, "num_frames"):
                call_kwargs["num_frames"] = num_frames
            try:
                import torch

                with torch.inference_mode():
                    try:
                        result = pipe(**call_kwargs)
                    except TypeError:
                        call_kwargs.pop("num_frames", None)
                        result = pipe(**call_kwargs)
                frames = getattr(result, "frames", None)
                if frames is None:
                    raise RuntimeError("Local video pipeline returned no frames.")
                if isinstance(frames, list) and frames and isinstance(frames[0], list):
                    frame_list = frames[0]
                else:
                    frame_list = list(frames)
                basis_mode = "i2v"
            except Exception as exc:
                from .cancellation import GenerationCancelled

                if isinstance(exc, GenerationCancelled):
                    raise
                logger.info(
                    "Native I2V failed (%s); falling back to basis morph",
                    exc,
                )
                frame_list, model_used = _generate_video_frames_from_basis(
                    prompt,
                    init_image,
                    model_cfg=cfg,
                    progress=progress,
                    cancel_event=cancel_event,
                    num_frames=num_frames,
                )
                basis_mode = "img2img_morph"
        else:
            _emit(
                progress,
                "Animating Studio basis with the local image model…",
                percent=72,
                title="Generating video",
            )
            frame_list, model_used = _generate_video_frames_from_basis(
                prompt,
                init_image,
                model_cfg=cfg,
                progress=progress,
                cancel_event=cancel_event,
                num_frames=num_frames,
            )
            basis_mode = "img2img_morph"
    else:
        pipe = local_media_manager.ensure_pipeline(
            kind="video",
            repo_id=repo_id,
            model_cfg=cfg,
            progress=progress,
            cancel_event=cancel_event,
        )

        _emit(
            progress,
            "Generating video frames (this can take several minutes)…",
            percent=75,
            title="Generating video",
        )
        _raise_if_cancelled(cancel_event)

        try:
            import torch

            call_kwargs = {
                "prompt": prompt,
                "num_inference_steps": steps,
            }
            if _pipe_accepts_kwarg(pipe, "num_frames"):
                call_kwargs["num_frames"] = num_frames

            with torch.inference_mode():
                try:
                    result = pipe(**call_kwargs)
                except TypeError:
                    call_kwargs.pop("num_frames", None)
                    result = pipe(**call_kwargs)

            frames = getattr(result, "frames", None)
            if frames is None:
                raise RuntimeError("Local video pipeline returned no frames.")
            if isinstance(frames, list) and frames and isinstance(frames[0], list):
                frame_list = frames[0]
            else:
                frame_list = list(frames)
        except Exception as exc:
            from .cancellation import GenerationCancelled

            if isinstance(exc, GenerationCancelled):
                raise
            raise RuntimeError(f"Local video generation error: {exc}") from exc

    _raise_if_cancelled(cancel_event)
    _emit(progress, "Encoding MP4…", percent=90, title="Generating video")
    video_bytes = _frames_to_mp4_bytes(frame_list, fps=fps)
    creation_id = f"doc_{uuid.uuid4().hex[:10]}"
    stored = write_media_bytes(creation_id, video_bytes, mime_type="video/mp4")
    return build_media_creation(
        modality="video",
        prompt=prompt,
        media_path=stored["mediaPath"],
        mime_type=stored["mimeType"],
        title=title_from_prompt(prompt),
        model_info={
            "provider": "huggingface",
            "repo_id": model_used,
            "modality": "video",
            "device": local_media_manager.status.get("device"),
            "num_frames": len(frame_list),
            "fps": fps,
            "basis": using_basis,
            "basis_mode": basis_mode,
        },
        creation_id=creation_id,
    )


def preload_local_models(
    model_cfg: dict[str, Any],
    *,
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
) -> dict[str, Any]:
    """
    Download / warm-load text, image, and video models into the HF cache.

    Unloads between slots so consumer GPUs are not forced to hold all three.
    Ends with no heavy pipeline resident (text weights may stay if already used).
    """
    from .hf_provider import text_model_cfg
    from .llm import model_manager

    cfg = normalize_huggingface_cfg(model_cfg)
    text_repo = cfg["text_model"]
    image_repo = cfg["image_model"]
    video_repo = cfg["video_model"]

    _emit(
        progress,
        f"Preloading text model ({text_repo})…",
        percent=5,
        title="Downloading models",
        phase="download",
    )
    _raise_if_cancelled(cancel_event)
    local_media_manager.unload()
    model_manager.set_progress_callback(progress)
    model_manager.set_cancel_event(cancel_event)
    try:
        model_manager.ensure_loaded(text_model_cfg(cfg))
    finally:
        model_manager.set_cancel_event(None)
    model_manager.unload()

    _emit(
        progress,
        f"Preloading image model ({image_repo})…",
        percent=40,
        title="Downloading models",
        phase="download",
    )
    _raise_if_cancelled(cancel_event)
    local_media_manager.ensure_pipeline(
        kind="image",
        repo_id=image_repo,
        model_cfg=cfg,
        progress=progress,
        cancel_event=cancel_event,
    )
    local_media_manager.unload()

    _emit(
        progress,
        f"Preloading video model ({video_repo})…",
        percent=70,
        title="Downloading models",
        phase="download",
    )
    _raise_if_cancelled(cancel_event)
    local_media_manager.ensure_pipeline(
        kind="video",
        repo_id=video_repo,
        model_cfg=cfg,
        progress=progress,
        cancel_event=cancel_event,
    )
    local_media_manager.unload()

    _emit(
        progress,
        "All local models downloaded (text, image, video).",
        percent=100,
        title="Models ready",
        phase="ready",
    )
    return {
        "textModel": text_repo,
        "imageModel": image_repo,
        "videoModel": video_repo,
    }
