"""Model / creation modality helpers (text | image | video)."""

from __future__ import annotations

import re
from typing import Any

Modality = str  # "text" | "image" | "video"

_IMAGE_ID_TOKENS: tuple[str, ...] = (
    "imagen",
    "image-generation",
    "flash-image",
    "pro-image",
    "-image-preview",
    "-image-generation",
    "nano-banana",
    "gpt-image",
    "flux",
    "seedream",
    "dall-e",
    "stable-diffusion",
    "sd-turbo",
    "sdxl",
    "dreamshaper",
    "text-to-image",
)

_VIDEO_ID_TOKENS: tuple[str, ...] = (
    "veo",
    "video-generation",
    "-video-preview",
    "-video-generation",
    "text-to-video",
    "zeroscope",
    "cogvideo",
    "modelscope",
    "animatediff",
    "seedance",
    "happyhorse",
    "wan-2",
    "flux-3-video",
)

# Non-generative surfaces still excluded from the studio model list
_SKIP_ID_TOKENS: tuple[str, ...] = (
    "embedding",
    "embed-content",
    "tts",
    "native-audio",
    "lyria",
    "aqa",
    "robotics",
    "computer-use",
    "-live-",
    "-live",
    "realtime",
)

_IMAGE_PHRASES: tuple[str, ...] = (
    "image generation",
    "generate images",
    "generates images",
    "image output",
    "text-to-image",
    "text to image",
)

_VIDEO_PHRASES: tuple[str, ...] = (
    "video generation",
    "generate videos",
    "generates videos",
    "video output",
    "text-to-video",
    "text to video",
)

_SKIP_PHRASES: tuple[str, ...] = (
    "text-to-speech",
    "text to speech",
    "native audio",
    "audio output",
    "speech synthesis",
    "music generation",
    "embedding",
)

# Prompt intent: strong signals that the user wants media, not a text document.
_IMAGE_PROMPT_RE = re.compile(
    r"""
    (?:
        \b(?:create|generate|make|draw|paint|render|design|produce)\b
        .{0,48}?
        \b(?:an?\s+)?(?:image|picture|illustration|artwork|drawing|photo|photograph|portrait)\b
      | \b(?:an?\s+)?(?:image|picture|illustration|artwork|drawing|photo|photograph)\s+of\b
      | \btext[\s\-]?to[\s\-]?image\b
      | \b(?:ai[\s\-]?)?(?:image|art)\s+prompt\b
    )
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

_VIDEO_PROMPT_RE = re.compile(
    r"""
    (?:
        \b(?:create|generate|make|render|produce|shoot|film)\b
        .{0,48}?
        \b(?:an?\s+)?(?:video|clip|animation|footage|movie|cinematic)\b
      | \b(?:turn|convert|transform|morph|change)\b
        .{0,48}?
        \b(?:into|to)\b
        .{0,24}?
        \b(?:an?\s+)?(?:video|clip|animation|footage|movie)\b
      | \b(?:an?\s+)?(?:video|clip|animation|footage)\s+of\b
      | \btext[\s\-]?to[\s\-]?video\b
      | \banimate\b
      | \bveo\b
    )
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

_TEXT_PROMPT_RE = re.compile(
    r"""
    (?:
        \b(?:write|draft|compose|summarize|explain|document)\b
        .{0,40}?
        \b(?:an?\s+|the\s+)?(?:essay|article|manual|guide|document|story|poem|letter|report|overview)\b
      | \b(?:quick\s+)?reference\s+(?:card|sheet)\b
      | \bkeybindings?\b
      | \bwalkthrough\b
      | \bcheat\s*sheet\b
    )
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)


def normalize_modality(value: Any, default: Modality = "text") -> Modality:
    raw = str(value or "").strip().lower()
    if raw in {"image", "img", "picture", "photo"}:
        return "image"
    if raw in {"video", "vid", "movie", "clip"}:
        return "video"
    if raw in {"text", "document", "doc", "markdown"}:
        return "text"
    return default


def classify_model_modality(
    model_id: str,
    *,
    display_name: str | None = None,
    description: str | None = None,
) -> Modality | None:
    """Return text/image/video, or None if the model should not appear in the studio list."""
    mid = (model_id or "").strip().lower().rstrip("/")
    if not mid:
        return None

    for token in _SKIP_ID_TOKENS:
        if token in mid:
            return None

    meta = f"{display_name or ''} {description or ''}".lower()
    for phrase in _SKIP_PHRASES:
        if phrase in meta:
            return None

    for token in _VIDEO_ID_TOKENS:
        if token in mid:
            return "video"
    for phrase in _VIDEO_PHRASES:
        if phrase in meta:
            return "video"

    for token in _IMAGE_ID_TOKENS:
        if token in mid:
            return "image"
    # Trailing -image (gemini-2.5-flash-image)
    if mid.endswith("-image") or mid.endswith("/image"):
        return "image"
    for phrase in _IMAGE_PHRASES:
        if phrase in meta:
            return "image"

    # OpenRouter / Gemini text chat models
    if "gemini" in mid or "/" in mid or "gpt" in mid or "claude" in mid or "llama" in mid:
        return "text"
    if "instruct" in mid or "chat" in mid:
        return "text"
    return "text"


def modality_label(modality: Modality) -> str:
    return {"text": "Text", "image": "Image", "video": "Video"}.get(modality, "Text")


def modality_indefinite(modality: Modality) -> str:
    label = modality_label(modality)
    article = "an" if label[:1].lower() in "aeiou" else "a"
    return f"{article} {label}"


def infer_prompt_modality(prompt: str) -> Modality | None:
    """
    Infer strong user intent from the prompt.

    Returns text/image/video when signals are clear, or None when ambiguous
    (do not block generation).
    """
    text = (prompt or "").strip()
    if not text:
        return None

    # Video before image: "create a video of an image morphing…" etc.
    if _VIDEO_PROMPT_RE.search(text):
        return "video"
    if _IMAGE_PROMPT_RE.search(text):
        return "image"
    if _TEXT_PROMPT_RE.search(text):
        return "text"
    return None


def resolve_generation_modality(
    prompt: str,
    *,
    basis_modality: str | None = None,
) -> Modality | None:
    """
    Choose text/image/video for a Studio CREATE.

    Clear prompt intent (including \"generate a video\" with an image basis →
    image-to-video) wins. Otherwise a media basis keeps the same modality.
    """
    prompt_mod = infer_prompt_modality(prompt)
    basis = (basis_modality or "").strip().lower()
    if basis not in {"image", "video"}:
        basis = ""

    if prompt_mod in {"image", "video"}:
        return prompt_mod
    if basis:
        return basis  # type: ignore[return-value]
    return prompt_mod


def suggested_model_ids_for_modality(modality: Modality) -> list[str]:
    """Curated Gemini model ids matching modality (best-effort suggestions)."""
    try:
        from .gemini_provider import SUGGESTED_GEMINI_MODELS
    except Exception:  # noqa: BLE001
        return []
    wanted = normalize_modality(modality, default="text")
    out: list[str] = []
    for item in SUGGESTED_GEMINI_MODELS:
        mid = str(item.get("repo_id") or "").strip()
        if not mid:
            continue
        mod = normalize_modality(item.get("modality"), default="text")
        if mod == wanted:
            out.append(mid)
    return out


def check_prompt_model_compatibility(
    prompt: str,
    model_id: str,
    *,
    provider: str = "gemini",
    gemini_cfg: dict[str, Any] | None = None,
    openrouter_cfg: dict[str, Any] | None = None,
    huggingface_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compare prompt intent with the selected backend.

    Gemini / OpenRouter / Hugging Face: three modality slots — Studio routes by
    prompt intent to the matching configured model.
    """
    prompt_mod = infer_prompt_modality(prompt)
    provider_l = (provider or "gemini").lower().strip()

    if provider_l in {"gemini", "google", "google-gemini"}:
        from .gemini_provider import resolve_gemini_model_for_modality

        routed_mod = prompt_mod or "text"
        model = resolve_gemini_model_for_modality(gemini_cfg, routed_mod)
        return {
            "ok": True,
            "promptModality": prompt_mod,
            "modelModality": routed_mod,
            "model": model,
            "routed": True,
        }

    if provider_l in {"openrouter", "open-router", "or"}:
        from .openrouter_provider import resolve_openrouter_model_for_modality

        routed_mod = prompt_mod or "text"
        model = resolve_openrouter_model_for_modality(openrouter_cfg, routed_mod)
        return {
            "ok": True,
            "promptModality": prompt_mod,
            "modelModality": routed_mod,
            "model": model,
            "routed": True,
        }

    if provider_l in {"huggingface", "hf", "local", "phi"}:
        from .hf_provider import resolve_hf_model_for_modality

        routed_mod = prompt_mod or "text"
        model = resolve_hf_model_for_modality(huggingface_cfg, routed_mod)
        return {
            "ok": True,
            "promptModality": prompt_mod,
            "modelModality": routed_mod,
            "model": model,
            "routed": True,
        }

    model_mod = classify_model_modality(model_id) or "text"
    if prompt_mod is None or prompt_mod == model_mod:
        return {
            "ok": True,
            "promptModality": prompt_mod,
            "modelModality": model_mod,
            "model": (model_id or "").strip(),
        }

    suggestions = suggested_model_ids_for_modality(prompt_mod)
    suggest_txt = (
        ", ".join(suggestions[:3])
        if suggestions
        else f"a {modality_label(prompt_mod)}-capable model"
    )
    where = f"Open Control Panel and switch to {suggest_txt}"

    error = (
        f"This prompt looks like {modality_indefinite(prompt_mod)} request, but the "
        f"selected model ({(model_id or '').strip() or 'unknown'}) is "
        f"{modality_label(model_mod)}-only. Generation stopped. {where}."
    )
    return {
        "ok": False,
        "error": error,
        "promptModality": prompt_mod,
        "modelModality": model_mod,
        "model": (model_id or "").strip(),
        "suggestions": suggestions,
    }
