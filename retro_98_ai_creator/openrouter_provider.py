"""OpenRouter API document generation (OpenAI-compatible chat completions)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Callable

from .creation_utils import build_text_creation_from_plain, finalize_creation, is_generic_studio_request
from .prompts import SYSTEM_MESSAGE, build_general_text_prompt, build_prompt

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

DEFAULT_OPENROUTER_TEXT_MODEL = "google/gemini-2.5-flash"
DEFAULT_OPENROUTER_IMAGE_MODEL = "google/gemini-2.5-flash-image"
DEFAULT_OPENROUTER_VIDEO_MODEL = "google/veo-2.0"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_LIST_LIMIT = 20

SUGGESTED_OPENROUTER_MODELS: list[dict[str, str]] = [
    {
        "repo_id": "google/gemini-2.5-flash",
        "label": "Gemini 2.5 Flash",
        "notes": "Recommended default via OpenRouter",
        "modality": "text",
    },
    {
        "repo_id": "google/gemini-2.5-pro",
        "label": "Gemini 2.5 Pro",
        "notes": "Recommended for highest accuracy",
        "modality": "text",
    },
    {
        "repo_id": "openai/gpt-4o-mini",
        "label": "GPT-4o Mini",
        "notes": "Fast & affordable OpenAI",
        "modality": "text",
    },
    {
        "repo_id": "openai/gpt-4o",
        "label": "GPT-4o",
        "notes": "Strong OpenAI multimodal",
        "modality": "text",
    },
    {
        "repo_id": "anthropic/claude-sonnet-4",
        "label": "Claude Sonnet 4",
        "notes": "Strong writing / documentation",
        "modality": "text",
    },
    {
        "repo_id": "deepseek/deepseek-chat",
        "label": "DeepSeek Chat",
        "notes": "Strong value JSON generation",
        "modality": "text",
    },
    {
        "repo_id": "meta-llama/llama-3.3-70b-instruct",
        "label": "Llama 3.3 70B Instruct",
        "notes": "Open-weight via OpenRouter",
        "modality": "text",
    },
    {
        "repo_id": "google/gemini-2.5-flash-image",
        "label": "Gemini 2.5 Flash Image",
        "notes": "Recommended image default",
        "modality": "image",
    },
    {
        "repo_id": "black-forest-labs/flux.2-pro",
        "label": "FLUX.2 Pro",
        "notes": "High-quality text-to-image",
        "modality": "image",
    },
    {
        "repo_id": "openai/gpt-image-1",
        "label": "GPT Image 1",
        "notes": "OpenAI image generation",
        "modality": "image",
    },
    {
        "repo_id": "bytedance-seed/seedream-4.5",
        "label": "Seedream 4.5",
        "notes": "ByteDance text-to-image",
        "modality": "image",
    },
    {
        "repo_id": "google/veo-2.0",
        "label": "Veo 2.0",
        "notes": "Recommended video default",
        "modality": "video",
    },
    {
        "repo_id": "google/veo-3.1",
        "label": "Veo 3.1",
        "notes": "Newer Google video model",
        "modality": "video",
    },
    {
        "repo_id": "google/veo-3.1-lite",
        "label": "Veo 3.1 Lite",
        "notes": "Faster / lower-cost Veo",
        "modality": "video",
    },
]


def resolve_api_key(openrouter_cfg: dict[str, Any] | None = None) -> str | None:
    openrouter_cfg = openrouter_cfg or {}
    key = (openrouter_cfg.get("api_key") or "").strip()
    return key or None


def normalize_openrouter_model(model_name: str | None) -> str:
    name = (model_name or "").strip()
    return name or DEFAULT_OPENROUTER_TEXT_MODEL


def resolve_openrouter_model_for_modality(
    openrouter_cfg: dict[str, Any] | None, modality: str
) -> str:
    """Pick the configured OpenRouter model id for text / image / video."""
    cfg = openrouter_cfg or {}
    mod = (modality or "text").lower().strip()
    if mod == "image":
        return (cfg.get("image_model") or "").strip() or DEFAULT_OPENROUTER_IMAGE_MODEL
    if mod == "video":
        return (cfg.get("video_model") or "").strip() or DEFAULT_OPENROUTER_VIDEO_MODEL
    return (cfg.get("text_model") or "").strip() or DEFAULT_OPENROUTER_TEXT_MODEL


def _openrouter_model_label(model_id: str, display_name: str | None = None) -> str:
    name = (display_name or "").strip()
    if name:
        return name
    mid = (model_id or "").strip()
    if "/" in mid:
        return mid.split("/", 1)[1] or mid
    return mid or "model"


def _openrouter_model_notes(item: dict[str, Any]) -> str:
    desc = str(item.get("description") or "").strip()
    if desc:
        # Keep picker rows readable
        one = " ".join(desc.split())
        return one[:72] + ("…" if len(one) > 72 else "")
    pricing = item.get("pricing") or {}
    prompt = pricing.get("prompt")
    try:
        p = float(prompt)
        if p >= 0:
            return f"${p * 1_000_000:.2f}/M prompt tokens"
    except (TypeError, ValueError):
        pass
    return "OpenRouter"


def _modality_from_openrouter_item(item: dict[str, Any], fallback: str) -> str | None:
    """Infer studio modality from Hub architecture + id heuristics."""
    from .modality import classify_model_modality

    mid = str(item.get("id") or "").strip()
    arch = item.get("architecture") or {}
    outs = arch.get("output_modalities") or []
    if isinstance(outs, str):
        outs = [outs]
    outs_l = {str(x).strip().lower() for x in outs if x}

    if "video" in outs_l:
        return "video"
    if "image" in outs_l and "text" not in outs_l:
        return "image"
    if "image" in outs_l and "text" in outs_l:
        # Multimodal image generators (e.g. flash-image) → image slot
        classified = classify_model_modality(
            mid,
            display_name=item.get("name"),
            description=item.get("description"),
        )
        if classified in {"image", "video"}:
            return classified
        if "image" in mid.lower() or "flux" in mid.lower():
            return "image"
    if outs_l == {"embeddings"} or "embedding" in mid.lower():
        return None
    if "audio" in outs_l and "text" not in outs_l and "image" not in outs_l:
        return None

    classified = classify_model_modality(
        mid,
        display_name=item.get("name"),
        description=item.get("description"),
    )
    if classified is None:
        return None
    return classified or fallback


def _fetch_openrouter_models(
    *,
    output_modality: str,
    sort: str = "most-popular",
    api_key: str | None = None,
    base_url: str = OPENROUTER_BASE_URL,
) -> list[dict[str, Any]]:
    """Fetch OpenRouter catalog for one output modality (server-sorted)."""
    import urllib.parse

    params = urllib.parse.urlencode(
        {
            "output_modalities": output_modality,
            "sort": sort,
        }
    )
    url = base_url.rstrip("/") + "/models?" + params
    headers = {
        "Accept": "application/json",
        "User-Agent": "retro-98-ai-creator",
        "X-Title": "Retro 98 AI Creator",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter network error: {exc.reason}") from exc

    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected OpenRouter models response: {body!r}")
    return [item for item in data if isinstance(item, dict)]


def list_available_openrouter_models(
    openrouter_cfg: dict[str, Any] | None = None,
    *,
    limit: int = OPENROUTER_LIST_LIMIT,
) -> list[dict[str, str]]:
    """
    Query OpenRouter for popular models per modality (``sort=most-popular``).

    Returns up to ``limit`` models for each of text / image / video.
    """
    cfg = openrouter_cfg or {}
    api_key = resolve_api_key(cfg)
    base_url = (cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL
    per = max(1, min(int(limit or OPENROUTER_LIST_LIMIT), 100))

    out: list[dict[str, str]] = []
    seen: set[str] = set()

    for modality, output_tag in (
        ("text", "text"),
        ("image", "image"),
        ("video", "video"),
    ):
        raw_items = _fetch_openrouter_models(
            output_modality=output_tag,
            sort="most-popular",
            api_key=api_key,
            base_url=base_url,
        )
        collected = 0
        for item in raw_items:
            if collected >= per:
                break
            mid = str(item.get("id") or "").strip()
            if not mid or mid in seen:
                continue
            inferred = _modality_from_openrouter_item(item, fallback=modality)
            if inferred != modality:
                continue
            seen.add(mid)
            collected += 1
            out.append(
                {
                    "repo_id": mid,
                    "label": _openrouter_model_label(mid, item.get("name")),
                    "notes": _openrouter_model_notes(item),
                    "modality": modality,
                }
            )

    if not out:
        raise RuntimeError("No OpenRouter models were returned.")
    return out


def merge_openrouter_model_suggestions(
    live: list[dict[str, str]] | None,
    curated: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Prefer live OpenRouter rows; keep curated entries missing from live."""
    curated = list(curated if curated is not None else SUGGESTED_OPENROUTER_MODELS)
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


def _chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    base_url: str,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "Retro 98 AI Creator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter network error: {exc.reason}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {body!r}") from exc

    if isinstance(content, list):
        # Some models return content parts
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text") or ""))
            elif isinstance(part, str):
                parts.append(part)
        content = "".join(parts)

    return str(content or "").strip()


def generate_with_openrouter(
    game: str,
    platform: str,
    creation_type: str,
    *,
    openrouter_cfg: dict[str, Any],
    system_extra: str = "",
    creation_description: str = "",
    progress: ProgressCallback | None = None,
    exact_title: bool = False,
    basis_media: dict[str, Any] | None = None,
    forced_modality: str | None = None,
) -> dict[str, Any]:
    """Call OpenRouter; prompt intent (or forced modality / media basis) selects the slot."""
    from .modality import infer_prompt_modality

    cfg = dict(openrouter_cfg or {})
    prompt_text = (creation_description or "").strip() or (game or "").strip()
    modality = (forced_modality or "").strip().lower() or infer_prompt_modality(
        prompt_text
    ) or "text"
    if basis_media and modality not in {"image", "video"}:
        modality = str(basis_media.get("modality") or "image")
    model_name = resolve_openrouter_model_for_modality(cfg, modality)

    if modality == "image":
        from .openrouter_media import generate_image_with_openrouter

        return generate_image_with_openrouter(
            prompt_text,
            openrouter_cfg=cfg,
            progress=progress,
            basis_media=basis_media,
        )
    if modality == "video":
        from .openrouter_media import generate_video_with_openrouter

        return generate_video_with_openrouter(
            prompt_text,
            openrouter_cfg=cfg,
            progress=progress,
            basis_media=basis_media,
        )

    return _generate_text_with_openrouter(
        game,
        platform,
        creation_type,
        openrouter_cfg=cfg,
        system_extra=system_extra,
        creation_description=creation_description,
        progress=progress,
        exact_title=exact_title,
        prompt_text=prompt_text,
        model_name=model_name,
    )


def _generate_text_with_openrouter(
    game: str,
    platform: str,
    creation_type: str,
    *,
    openrouter_cfg: dict[str, Any],
    system_extra: str = "",
    creation_description: str = "",
    progress: ProgressCallback | None = None,
    exact_title: bool = False,
    prompt_text: str = "",
    model_name: str = DEFAULT_OPENROUTER_TEXT_MODEL,
) -> dict[str, Any]:
    """Text generation path (freeform Prompt or classic structured document)."""

    def emit(message: str, percent: float | None = None, **extra: Any) -> None:
        if not progress:
            return
        from .cancellation import GenerationCancelled

        payload: dict[str, Any] = {
            "message": message,
            "phase": "generate",
            "title": "Generating document",
        }
        if percent is not None:
            payload["percent"] = percent
        payload.update(extra)
        try:
            progress(payload)
        except GenerationCancelled:
            raise
        except Exception:  # noqa: BLE001
            pass

    api_key = resolve_api_key(openrouter_cfg)
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key missing. Paste your key in Control Panel → AI Model (OpenRouter)."
        )

    temperature = float(
        openrouter_cfg.get("temperature")
        if openrouter_cfg.get("temperature") is not None
        else 0.0
    )
    base_url = (
        (openrouter_cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL
    )

    emit(f"Contacting OpenRouter ({model_name})…", percent=10)
    generic = is_generic_studio_request(game, platform, creation_type)

    if generic:
        prompt = build_general_text_prompt(prompt_text, system_extra=system_extra)
        system = (
            "You are a helpful creative AI assistant. "
            "Follow the user's prompt carefully. Prefer clear, well-structured output."
        )
    else:
        prompt = build_prompt(
            game,
            platform,
            creation_type,
            system_extra=system_extra,
            creation_description=creation_description,
            with_web_search=False,
            exact_title=exact_title,
        )
        system = SYSTEM_MESSAGE

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    emit("Calling OpenRouter…", percent=40)
    try:
        response_text = _chat_completion(
            api_key=api_key,
            model=model_name,
            messages=messages,
            temperature=temperature,
            base_url=base_url,
        )
    except Exception as exc:
        from .cancellation import GenerationCancelled

        if isinstance(exc, GenerationCancelled):
            raise
        raise RuntimeError(f"OpenRouter API error: {exc}") from exc

    if not response_text:
        raise RuntimeError("OpenRouter returned an empty response.")

    if generic:
        emit("Formatting response…", percent=85)
        return build_text_creation_from_plain(
            response_text,
            prompt=prompt_text,
            model_info={
                "provider": "openrouter",
                "repo_id": model_name,
                "modality": "text",
                "temperature": temperature,
                "google_search": False,
            },
        )

    emit("Parsing OpenRouter JSON…", percent=85)
    return finalize_creation(
        response_text,
        game,
        platform,
        creation_type,
        model_info={
            "provider": "openrouter",
            "repo_id": model_name,
            "modality": "text",
            "temperature": temperature,
            "google_search": False,
        },
        grounding_sources=None,
        exact_title=exact_title,
        prompt=prompt_text,
    )
