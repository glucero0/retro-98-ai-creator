"""Google Gemini API document generation."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable

from .creation_utils import finalize_creation
from .prompts import build_prompt

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Retired model IDs still present in older configs
DEPRECATED_GEMINI_MODELS: dict[str, str] = {
    "gemini-2.0-flash": "gemini-2.5-flash",
    "gemini-2.0-flash-001": "gemini-2.5-flash",
    "models/gemini-2.0-flash": "gemini-2.5-flash",
}

SUGGESTED_GEMINI_MODELS: list[dict[str, str]] = [
    {
        "repo_id": "gemini-2.5-flash",
        "label": "Gemini 2.5 Flash (default)",
        "notes": "Fast, strong JSON — recommended",
    },
    {
        "repo_id": "gemini-2.5-pro",
        "label": "Gemini 2.5 Pro",
        "notes": "Higher quality, slower / costlier",
    },
    {
        "repo_id": "gemini-flash-latest",
        "label": "Gemini Flash (latest alias)",
        "notes": "Google's current flash alias if available",
    },
]


def normalize_gemini_model(model_name: str | None) -> str:
    name = (model_name or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    return DEPRECATED_GEMINI_MODELS.get(name, name)


def resolve_api_key(gemini_cfg: dict[str, Any] | None = None) -> str | None:
    gemini_cfg = gemini_cfg or {}
    key = (
        (gemini_cfg.get("api_key") or "").strip()
        or os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    return key or None


def _extract_grounding_sources(response: Any) -> list[dict[str, str]]:
    """Best-effort extraction of web citations from Gemini grounding metadata."""
    sources: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(title: str | None, url: str | None) -> None:
        if not url:
            return
        key = url.strip()
        if not key or key in seen:
            return
        seen.add(key)
        sources.append({"title": (title or url).strip(), "url": key})

    try:
        cands = getattr(response, "candidates", None) or []
        if not cands:
            return sources
        meta = getattr(cands[0], "grounding_metadata", None)
        if not meta:
            return sources

        for chunk in getattr(meta, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            if web and getattr(web, "uri", None):
                add(getattr(web, "title", None), web.uri)

        # Some responses only populate the search entry-point HTML
        entry = getattr(meta, "search_entry_point", None)
        html = getattr(entry, "rendered_content", None) if entry else None
        if isinstance(html, str) and html:
            for href, label in re.findall(
                r'href="([^"]+)"[^>]*>([^<]*)</a>', html, flags=re.IGNORECASE
            ):
                add(label or href, href)

        # Last resort: expose the queries that were searched
        if not sources:
            from urllib.parse import quote_plus

            for query in getattr(meta, "web_search_queries", None) or []:
                q = str(query).strip()
                if q:
                    add(f"Search: {q}", f"https://www.google.com/search?q={quote_plus(q)}")
    except Exception:  # noqa: BLE001
        logger.debug("Could not parse grounding metadata", exc_info=True)

    return sources


def generate_with_gemini(
    game: str,
    platform: str,
    creation_type: str,
    *,
    gemini_cfg: dict[str, Any],
    system_extra: str = "",
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Call Gemini (optional Google Search grounding) and return a creation dict."""

    def emit(message: str, percent: float | None = None, **extra: Any) -> None:
        if not progress:
            return
        payload: dict[str, Any] = {"message": message, "phase": "generate", "title": "Generating document"}
        if percent is not None:
            payload["percent"] = percent
        payload.update(extra)
        try:
            progress(payload)
        except Exception:  # noqa: BLE001
            pass

    api_key = resolve_api_key(gemini_cfg)
    if not api_key:
        raise RuntimeError(
            "Gemini API key missing. Set GEMINI_API_KEY in the environment, "
            "or paste your key in Control Panel → AI Model (Gemini)."
        )

    model_name = normalize_gemini_model(gemini_cfg.get("model"))
    use_search = gemini_cfg.get("google_search", True)
    temperature = float(gemini_cfg.get("temperature") if gemini_cfg.get("temperature") is not None else 0.4)

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Run:\n  pip install google-genai"
        ) from exc

    emit(f"Contacting Gemini ({model_name})…", percent=10)
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(
        game,
        platform,
        creation_type,
        system_extra=system_extra,
        with_web_search=bool(use_search),
    )

    response_text = ""
    grounding_sources: list[dict[str, str]] = []
    search_used = False

    def _call(*, with_search: bool) -> str:
        nonlocal grounding_sources
        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
        }
        # Gemini 2.5 rejects tools + response_mime_type=application/json together.
        # With search: omit mime type and parse JSON from text.
        # Without search: keep JSON mime for stricter structured output.
        if with_search:
            config_kwargs["tools"] = [
                types.Tool(google_search=types.GoogleSearch())
            ]
        else:
            config_kwargs["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        if with_search:
            grounding_sources = _extract_grounding_sources(response)
        return (response.text or "").strip()

    try:
        if use_search:
            emit("Gemini + Google Search grounding…", percent=35)
            try:
                response_text = _call(with_search=True)
                search_used = True
            except Exception as search_err:
                logger.warning(
                    "Gemini search-grounded call failed; retrying without search: %s",
                    search_err,
                )
                emit("Search grounding unavailable — using direct Gemini…", percent=50)
                response_text = _call(with_search=False)
                search_used = False
        else:
            emit("Calling Gemini…", percent=40)
            response_text = _call(with_search=False)
    except Exception as exc:
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")

    emit("Parsing Gemini JSON…", percent=85)
    return finalize_creation(
        response_text,
        game,
        platform,
        creation_type,
        model_info={
            "provider": "gemini",
            "repo_id": model_name,
            "google_search": bool(search_used),
        },
        grounding_sources=grounding_sources or None,
    )
