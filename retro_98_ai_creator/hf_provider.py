"""Hugging Face local provider — routes text / image / video by prompt intent."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from .config import (
    DEFAULT_HF_IMAGE_MODEL,
    DEFAULT_HF_TEXT_MODEL,
    DEFAULT_HF_VIDEO_MODEL,
    SUGGESTED_MODELS,
    normalize_huggingface_cfg,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

HF_HUB_MODELS_URL = "https://huggingface.co/api/models"
HF_LIST_LIMIT = 20

# Hub pipeline tags used for each Control Panel modality slot
HF_PIPELINE_TAGS: dict[str, tuple[str, ...]] = {
    "text": ("text-generation",),
    "image": ("text-to-image",),
    "video": ("text-to-video",),
}


def normalize_hf_model(model_name: str | None, *, default: str = DEFAULT_HF_TEXT_MODEL) -> str:
    name = (model_name or "").strip()
    return name or default


def resolve_hf_model_for_modality(
    hf_cfg: dict[str, Any] | None, modality: str
) -> str:
    """Pick the configured local HF repo id for text / image / video."""
    cfg = normalize_huggingface_cfg(hf_cfg)
    mod = (modality or "text").lower().strip()
    if mod == "image":
        return normalize_hf_model(cfg.get("image_model"), default=DEFAULT_HF_IMAGE_MODEL)
    if mod == "video":
        return normalize_hf_model(cfg.get("video_model"), default=DEFAULT_HF_VIDEO_MODEL)
    return normalize_hf_model(
        cfg.get("text_model") or cfg.get("repo_id"),
        default=DEFAULT_HF_TEXT_MODEL,
    )


def text_model_cfg(hf_cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Config slice for the text causal-LM loader (``repo_id`` = text slot)."""
    cfg = normalize_huggingface_cfg(hf_cfg)
    out = dict(cfg)
    out["repo_id"] = cfg["text_model"]
    return out


def _format_download_count(count: Any) -> str:
    try:
        n = int(count or 0)
    except (TypeError, ValueError):
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M downloads"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k downloads"
    if n > 0:
        return f"{n} downloads"
    return ""


def _hf_model_label(repo_id: str) -> str:
    rid = (repo_id or "").strip()
    if "/" in rid:
        return rid.split("/", 1)[1] or rid
    return rid or "model"


def _fetch_hub_pipeline_models(
    pipeline_tag: str,
    *,
    limit: int,
    token: str | None,
) -> list[dict[str, Any]]:
    """Fetch top Hub models for a pipeline tag, ranked by downloads."""
    params = urllib.parse.urlencode(
        {
            "pipeline_tag": pipeline_tag,
            "sort": "downloads",
            "direction": "-1",
            "limit": str(max(1, min(int(limit), 100))),
        }
    )
    url = f"{HF_HUB_MODELS_URL}?{params}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "retro-98-ai-creator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise RuntimeError(f"Hugging Face Hub HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Hugging Face Hub network error: {exc.reason}") from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hugging Face Hub returned invalid JSON.") from exc
    if not isinstance(data, list):
        raise RuntimeError(
            f"Unexpected Hub response for {pipeline_tag}: {type(data).__name__}"
        )
    return [item for item in data if isinstance(item, dict)]


def list_available_hf_models(
    hf_cfg: dict[str, Any] | None = None,
    *,
    limit: int = HF_LIST_LIMIT,
) -> list[dict[str, str]]:
    """
    Query Hugging Face Hub for popular models per modality (downloads descending).

    Returns up to ``limit`` models for each of text / image / video.
    """
    cfg = normalize_huggingface_cfg(hf_cfg)
    token = (cfg.get("hf_token") or "").strip() or None
    per = max(1, min(int(limit or HF_LIST_LIMIT), 100))

    out: list[dict[str, str]] = []
    seen: set[str] = set()

    for modality, tags in HF_PIPELINE_TAGS.items():
        collected: list[dict[str, str]] = []
        for tag in tags:
            if len(collected) >= per:
                break
            raw_items = _fetch_hub_pipeline_models(tag, limit=per, token=token)
            for item in raw_items:
                if len(collected) >= per:
                    break
                repo_id = str(item.get("id") or item.get("modelId") or "").strip()
                if not repo_id or repo_id in seen:
                    continue
                downloads = item.get("downloads")
                likes = item.get("likes")
                notes_bits = []
                dl_txt = _format_download_count(downloads)
                if dl_txt:
                    notes_bits.append(dl_txt)
                try:
                    like_n = int(likes or 0)
                except (TypeError, ValueError):
                    like_n = 0
                if like_n > 0:
                    notes_bits.append(f"{like_n} likes")
                seen.add(repo_id)
                collected.append(
                    {
                        "repo_id": repo_id,
                        "label": _hf_model_label(repo_id),
                        "notes": " · ".join(notes_bits),
                        "modality": modality,
                    }
                )
        out.extend(collected)

    if not out:
        raise RuntimeError("No Hugging Face models were returned from the Hub.")
    return out


def merge_hf_model_suggestions(
    live: list[dict[str, str]] | None,
    curated: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Prefer live Hub rows; keep curated entries that are missing from live."""
    curated = list(curated if curated is not None else SUGGESTED_MODELS)
    live = list(live or [])
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in live + curated:
        mid = str(item.get("repo_id") or "").strip()
        if not mid or mid in seen:
            continue
        seen.add(mid)
        row = dict(item)
        row.setdefault("modality", "text")
        out.append(row)
    return out


def generate_with_huggingface(
    game: str,
    platform: str,
    creation_type: str,
    *,
    model_cfg: dict[str, Any],
    system_extra: str = "",
    creation_description: str = "",
    progress: ProgressCallback | None = None,
    exact_title: bool = False,
    cancel_event: Any = None,
    basis_media: dict[str, Any] | None = None,
    forced_modality: str | None = None,
) -> dict[str, Any]:
    """Route local HF generation by prompt modality (text / image / video)."""
    from .modality import infer_prompt_modality

    cfg = normalize_huggingface_cfg(model_cfg)
    prompt_text = (creation_description or "").strip() or (game or "").strip()
    modality = (forced_modality or "").strip().lower() or infer_prompt_modality(
        prompt_text
    ) or "text"
    if basis_media and modality not in {"image", "video"}:
        modality = str(basis_media.get("modality") or "image")

    if modality == "image":
        from .hf_media import generate_image_with_hf

        return generate_image_with_hf(
            prompt_text,
            model_cfg=cfg,
            progress=progress,
            cancel_event=cancel_event,
            basis_media=basis_media,
        )
    if modality == "video":
        from .hf_media import generate_video_with_hf

        return generate_video_with_hf(
            prompt_text,
            model_cfg=cfg,
            progress=progress,
            cancel_event=cancel_event,
            basis_media=basis_media,
        )

    from .llm import model_manager

    model_manager.set_progress_callback(progress)
    model_manager.set_cancel_event(cancel_event)
    try:
        # Free diffusion pipelines before loading a large causal LM
        try:
            from .hf_media import local_media_manager

            local_media_manager.unload()
        except Exception:  # noqa: BLE001
            logger.debug("Could not unload local media pipelines", exc_info=True)

        return model_manager.generate_creation(
            game=game,
            platform=platform,
            creation_type=creation_type,
            model_cfg=text_model_cfg(cfg),
            system_extra=system_extra,
            creation_description=creation_description,
            exact_title=exact_title,
        )
    finally:
        model_manager.set_cancel_event(None)
