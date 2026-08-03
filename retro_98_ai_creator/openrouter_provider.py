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

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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
]


def resolve_api_key(openrouter_cfg: dict[str, Any] | None = None) -> str | None:
    openrouter_cfg = openrouter_cfg or {}
    key = (openrouter_cfg.get("api_key") or "").strip()
    return key or None


def normalize_openrouter_model(model_name: str | None) -> str:
    name = (model_name or DEFAULT_OPENROUTER_MODEL).strip()
    return name or DEFAULT_OPENROUTER_MODEL


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
) -> dict[str, Any]:
    """Call OpenRouter chat completions and return a creation dict."""

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

    model_name = normalize_openrouter_model(openrouter_cfg.get("model"))
    temperature = float(
        openrouter_cfg.get("temperature")
        if openrouter_cfg.get("temperature") is not None
        else 0.0
    )
    base_url = (openrouter_cfg.get("base_url") or OPENROUTER_BASE_URL).strip() or OPENROUTER_BASE_URL

    emit(f"Contacting OpenRouter ({model_name})…", percent=10)
    prompt_text = (creation_description or "").strip() or (game or "").strip()
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
            "google_search": False,
        },
        grounding_sources=None,
        exact_title=exact_title,
        prompt=prompt_text,
    )
