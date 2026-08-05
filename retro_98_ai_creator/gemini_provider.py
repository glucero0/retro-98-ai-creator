"""Google Gemini API document generation (optional two-pass search + verify)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from .creation_utils import (
    build_media_creation,
    build_text_creation_from_plain,
    extract_json_object,
    finalize_creation,
    is_ambiguous,
    is_game_not_found,
    is_generic_studio_request,
    normalize_source_snippets,
    title_from_prompt,
)
from .media_store import write_media_bytes
from .modality import classify_model_modality
from .prompts import (
    build_general_text_prompt,
    build_prompt,
    build_search_extract_prompt,
    build_verification_prompt,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Any], None]

DEFAULT_GEMINI_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_GEMINI_VIDEO_MODEL = "veo-2.0-generate-001"

SUGGESTED_GEMINI_MODELS: list[dict[str, str]] = [
    {
        "repo_id": "gemini-2.5-flash",
        "label": "Gemini 2.5 Flash (default text)",
        "notes": "Cheapest balanced text — Search + two-pass",
        "modality": "text",
    },
    {
        "repo_id": "gemini-2.5-pro",
        "label": "Gemini 2.5 Pro",
        "notes": "Higher quality text",
        "modality": "text",
    },
    {
        "repo_id": "gemini-flash-latest",
        "label": "Gemini Flash (latest alias)",
        "notes": "Google's current flash alias if available",
        "modality": "text",
    },
    {
        "repo_id": "gemini-2.5-flash-image",
        "label": "Gemini 2.5 Flash Image (default)",
        "notes": "Cheapest native image generation",
        "modality": "image",
    },
    {
        "repo_id": "gemini-3.1-flash-image-preview",
        "label": "Gemini 3.1 Flash Image Preview",
        "notes": "Newer image preview (usually costlier)",
        "modality": "image",
    },
    {
        "repo_id": "veo-2.0-generate-001",
        "label": "Veo 2.0 Generate (default)",
        "notes": "Cheaper text-to-video",
        "modality": "video",
    },
    {
        "repo_id": "veo-3.1-generate-preview",
        "label": "Veo 3.1 Generate Preview",
        "notes": "Newer video preview (usually costlier)",
        "modality": "video",
    },
]


def _gemini_model_id(name: str | None) -> str:
    raw = (name or "").strip()
    if raw.startswith("models/"):
        raw = raw[len("models/") :]
    return raw


def _gemini_model_notes(model_id: str, description: str | None = None) -> str:
    mid = model_id.lower()
    if "flash-lite" in mid or "flashlite" in mid:
        return "Fastest / cheapest Flash variant"
    if "flash" in mid and "pro" not in mid:
        if "2.5" in mid:
            return "Best balance — recommended with Search + two-pass"
        return "Fast Flash model"
    if "pro" in mid:
        return "Higher quality — good for accuracy"
    desc = (description or "").strip()
    if desc and len(desc) < 80:
        return desc
    return "Available for your API key"


def _gemini_model_label(model_id: str, display_name: str | None = None) -> str:
    if display_name and display_name.strip():
        return display_name.strip()
    # gemini-2.5-flash → Gemini 2.5 Flash
    parts = model_id.replace("_", "-").split("-")
    titled = " ".join(p.upper() if p in {"tts", "it"} else p.capitalize() for p in parts)
    return titled.replace("Gemini", "Gemini", 1)


# Tokens matched against the model id only — non-studio surfaces to skip.
_GEMINI_ID_SKIP_TOKENS: tuple[str, ...] = (
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

# Phrases matched against display name + description (not bare "video"/"image").
_GEMINI_SKIP_PHRASES: tuple[str, ...] = (
    "text-to-speech",
    "text to speech",
    "native audio",
    "audio output",
    "speech synthesis",
    "music generation",
)


def _is_studio_gemini_model(
    model_id: str,
    *,
    display_name: str | None = None,
    description: str | None = None,
    supported_actions: list[str] | None = None,
) -> bool:
    """True for Gemini text / image / video models usable in the studio."""
    mid = (model_id or "").strip().lower().rstrip("/")
    if not mid:
        return False
    # Allow imagen / veo even without "gemini" in the id
    modality = classify_model_modality(
        mid, display_name=display_name, description=description
    )
    if modality is None:
        return False
    if "gemini" not in mid and modality == "text":
        return False

    for token in _GEMINI_ID_SKIP_TOKENS:
        if token in mid:
            return False

    meta = f"{display_name or ''} {description or ''}".lower()
    for phrase in _GEMINI_SKIP_PHRASES:
        if phrase in meta:
            return False

    actions = [str(a).lower() for a in (supported_actions or [])]
    if actions and modality == "text":
        joined = "".join(actions).replace("_", "")
        # Some listings omit actions; only enforce when present
        if "generatecontent" not in joined and "predict" not in joined:
            # video/image may use other action names — already classified
            if modality == "text":
                return False

    return True


def _is_text_generation_gemini_model(
    model_id: str,
    *,
    display_name: str | None = None,
    description: str | None = None,
    supported_actions: list[str] | None = None,
) -> bool:
    """True only for text-modality Gemini models (tests / callers)."""
    if not _is_studio_gemini_model(
        model_id,
        display_name=display_name,
        description=description,
        supported_actions=supported_actions,
    ):
        return False
    return (
        classify_model_modality(
            model_id, display_name=display_name, description=description
        )
        == "text"
    )


def list_available_gemini_models(api_key: str) -> list[dict[str, str]]:
    """Query Google for text/image/video models available to this API key."""
    key = (api_key or "").strip()
    if not key:
        raise RuntimeError("Gemini API key required to list available models.")

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Run:\n  pip install google-genai"
        ) from exc

    client = genai.Client(api_key=key)
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    for model in client.models.list():
        model_id = _gemini_model_id(getattr(model, "name", None))
        if not model_id or model_id in seen:
            continue
        display = getattr(model, "display_name", None)
        description = getattr(model, "description", None)
        actions = list(getattr(model, "supported_actions", None) or [])
        if not _is_studio_gemini_model(
            model_id,
            display_name=display,
            description=description,
            supported_actions=actions,
        ):
            continue
        modality = classify_model_modality(
            model_id, display_name=display, description=description
        ) or "text"
        seen.add(model_id)
        out.append(
            {
                "repo_id": model_id,
                "label": _gemini_model_label(model_id, display),
                "notes": _gemini_model_notes(model_id, description),
                "modality": modality,
            }
        )

    def sort_key(item: dict[str, str]) -> tuple:
        mid = item["repo_id"].lower()
        modality = item.get("modality") or "text"
        mod_tier = {"text": 0, "image": 1, "video": 2}.get(modality, 9)
        tier = 50
        if "2.5-flash" in mid and "lite" not in mid and "image" not in mid:
            tier = 0
        elif "2.5-pro" in mid and "image" not in mid:
            tier = 1
        elif "flash-latest" in mid or mid.endswith("flash"):
            tier = 2
        elif "pro" in mid:
            tier = 3
        elif "imagen" in mid or "flash-image" in mid or "image" in mid:
            tier = 10
        elif "veo" in mid:
            tier = 20
        elif "exp" in mid or "preview" in mid:
            tier = 80
        return (mod_tier, tier, mid)

    out.sort(key=sort_key)
    if not out:
        raise RuntimeError(
            "No Gemini studio models were returned for this API key."
        )
    return out


def normalize_gemini_model(model_name: str | None) -> str:
    name = (model_name or "").strip()
    return name or DEFAULT_GEMINI_TEXT_MODEL


def resolve_gemini_model_for_modality(
    gemini_cfg: dict[str, Any] | None, modality: str
) -> str:
    """Pick the configured model id for text / image / video."""
    cfg = gemini_cfg or {}
    mod = (modality or "text").lower().strip()
    if mod == "image":
        return (cfg.get("image_model") or "").strip() or DEFAULT_GEMINI_IMAGE_MODEL
    if mod == "video":
        return (cfg.get("video_model") or "").strip() or DEFAULT_GEMINI_VIDEO_MODEL
    return (cfg.get("text_model") or "").strip() or DEFAULT_GEMINI_TEXT_MODEL


def resolve_api_key(gemini_cfg: dict[str, Any] | None = None) -> str | None:
    gemini_cfg = gemini_cfg or {}
    key = (gemini_cfg.get("api_key") or "").strip()
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


def _two_pass_enabled(gemini_cfg: dict[str, Any], *, use_search: bool) -> bool:
    """Two-pass verify defaults on whenever Google Search grounding is enabled."""
    if not use_search:
        return False
    flag = gemini_cfg.get("two_pass_verify")
    if flag is None:
        return True
    return bool(flag)


def generate_with_gemini(
    game: str,
    platform: str,
    creation_type: str,
    *,
    gemini_cfg: dict[str, Any],
    system_extra: str = "",
    creation_description: str = "",
    progress: ProgressCallback | None = None,
    exact_title: bool = False,
    basis_media: dict[str, Any] | None = None,
    forced_modality: str | None = None,
) -> dict[str, Any]:
    """Call Gemini; prompt intent (or forced modality / media basis) selects the slot."""
    from .modality import infer_prompt_modality

    cfg = dict(gemini_cfg or {})
    prompt_text = (creation_description or "").strip() or (game or "").strip()
    modality = (forced_modality or "").strip().lower() or infer_prompt_modality(
        prompt_text
    ) or "text"
    if basis_media and modality not in {"image", "video"}:
        modality = str(basis_media.get("modality") or "image")
    model_name = resolve_gemini_model_for_modality(cfg, modality)

    if modality == "image":
        from .gemini_media import generate_image_with_gemini

        return generate_image_with_gemini(
            prompt_text,
            gemini_cfg=cfg,
            progress=progress,
            basis_media=basis_media,
        )
    if modality == "video":
        from .gemini_media import generate_video_with_gemini

        return generate_video_with_gemini(
            prompt_text,
            gemini_cfg=cfg,
            progress=progress,
            basis_media=basis_media,
        )

    return _generate_text_with_gemini(
        game,
        platform,
        creation_type,
        gemini_cfg=cfg,
        system_extra=system_extra,
        creation_description=creation_description,
        progress=progress,
        exact_title=exact_title,
        prompt_text=prompt_text,
        model_name=model_name,
    )


def _generate_text_with_gemini(
    game: str,
    platform: str,
    creation_type: str,
    *,
    gemini_cfg: dict[str, Any],
    system_extra: str = "",
    creation_description: str = "",
    progress: ProgressCallback | None = None,
    exact_title: bool = False,
    prompt_text: str = "",
    model_name: str = DEFAULT_GEMINI_TEXT_MODEL,
) -> dict[str, Any]:
    """Text generation path (freeform Prompt or classic structured document)."""

    def emit(message: str, percent: float | None = None, **extra: Any) -> None:
        if not progress:
            return
        from .cancellation import GenerationCancelled

        payload: dict[str, Any] = {
            "message": message,
            "phase": "generate",
            "title": extra.pop("title", None) or "Generating text",
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

    api_key = resolve_api_key(gemini_cfg)
    if not api_key:
        raise RuntimeError(
            "Gemini API key missing. Paste your key in Control Panel → AI Model (Gemini)."
        )

    use_search = gemini_cfg.get("google_search", True)
    temperature = float(
        gemini_cfg.get("temperature") if gemini_cfg.get("temperature") is not None else 0.0
    )
    generic = is_generic_studio_request(game, platform, creation_type)
    if generic:
        use_search = False
    two_pass = _two_pass_enabled(gemini_cfg, use_search=bool(use_search)) and not generic

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Run:\n  pip install google-genai"
        ) from exc

    emit(f"Contacting Gemini ({model_name})…", percent=10)
    client = genai.Client(api_key=api_key)

    grounding_sources: list[dict[str, str]] = []
    search_used = False

    def _call(
        prompt: str,
        *,
        with_search: bool,
        call_temperature: float,
        json_mime: bool,
    ) -> str:
        nonlocal grounding_sources
        config_kwargs: dict[str, Any] = {
            "temperature": call_temperature,
        }
        if with_search:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        elif json_mime:
            config_kwargs["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        if with_search:
            grounding_sources = _extract_grounding_sources(response)
        return (response.text or "").strip()

    if generic:
        emit("Calling Gemini…", percent=40)
        try:
            response_text = _call(
                build_general_text_prompt(prompt_text, system_extra=system_extra),
                with_search=False,
                call_temperature=temperature,
                json_mime=False,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc
        if not response_text:
            raise RuntimeError("Gemini returned an empty response.")
        emit("Formatting response…", percent=90)
        return build_text_creation_from_plain(
            response_text,
            prompt=prompt_text,
            model_info={
                "provider": "gemini",
                "repo_id": model_name,
                "modality": "text",
                "temperature": temperature,
                "google_search": False,
                "two_pass_verify": False,
            },
        )

    if two_pass:
        pass1_prompt = build_search_extract_prompt(
            game,
            platform,
            creation_type,
            system_extra=system_extra,
            creation_description=creation_description,
            exact_title=exact_title,
        )
    else:
        pass1_prompt = build_prompt(
            game,
            platform,
            creation_type,
            system_extra=system_extra,
            creation_description=creation_description,
            with_web_search=bool(use_search),
            exact_title=exact_title,
        )

    response_text = ""
    try:
        if use_search:
            emit(
                "Pass 1: Gemini + Google Search (extract)…"
                if two_pass
                else "Gemini + Google Search grounding…",
                percent=30,
                title="Generating document",
            )
            try:
                response_text = _call(
                    pass1_prompt,
                    with_search=True,
                    call_temperature=temperature,
                    json_mime=False,
                )
                search_used = True
            except Exception as search_err:
                logger.warning(
                    "Gemini search-grounded call failed; retrying without search: %s",
                    search_err,
                )
                emit("Search grounding unavailable — using direct Gemini…", percent=45)
                two_pass = False
                response_text = _call(
                    build_prompt(
                        game,
                        platform,
                        creation_type,
                        system_extra=system_extra,
                        creation_description=creation_description,
                        with_web_search=False,
                        exact_title=exact_title,
                    ),
                    with_search=False,
                    call_temperature=temperature,
                    json_mime=True,
                )
                search_used = False
        else:
            emit("Calling Gemini…", percent=40, title="Generating document")
            response_text = _call(
                pass1_prompt,
                with_search=False,
                call_temperature=temperature,
                json_mime=True,
            )
    except Exception as exc:
        from .cancellation import GenerationCancelled

        if isinstance(exc, GenerationCancelled):
            raise
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")

    pass1_parsed = extract_json_object(response_text)
    if is_ambiguous(pass1_parsed) or is_game_not_found(pass1_parsed):
        emit("Parsing Gemini JSON…", percent=90, title="Generating document")
        return finalize_creation(
            response_text,
            game,
            platform,
            creation_type,
            model_info={
                "provider": "gemini",
                "repo_id": model_name,
                "modality": "text",
                "temperature": temperature,
                "google_search": bool(search_used),
                "two_pass_verify": False,
            },
            grounding_sources=grounding_sources or None,
            exact_title=exact_title,
            prompt=prompt_text,
        )

    verified = False
    if two_pass and isinstance(pass1_parsed, dict):
        snippets = normalize_source_snippets(pass1_parsed.get("sourceSnippets"))
        if not snippets:
            logger.warning(
                "Pass 1 returned no sourceSnippets — skipping verification pass."
            )
            emit("Pass 1 had no snippets — skipping verification…", percent=75)
        else:
            emit("Pass 2: Gemini verification (temperature 0)…", percent=65)
            verify_prompt = build_verification_prompt(
                game,
                platform,
                creation_type,
                candidate_document=pass1_parsed,
                source_snippets=snippets,
                creation_description=creation_description,
                system_extra=system_extra,
            )
            try:
                verified_text = _call(
                    verify_prompt,
                    with_search=False,
                    call_temperature=0.0,
                    json_mime=True,
                )
            except Exception as verify_err:
                logger.warning(
                    "Pass 2 verification failed; using Pass 1 output: %s", verify_err
                )
                emit("Verification unavailable — using Pass 1 extract…", percent=80)
                verified_text = ""

            if verified_text:
                verified_parsed = extract_json_object(verified_text)
                if (
                    verified_parsed
                    and not is_ambiguous(verified_parsed)
                    and not is_game_not_found(verified_parsed)
                    and str(verified_parsed.get("game") or "").strip()
                ):
                    if not normalize_source_snippets(verified_parsed.get("sourceSnippets")):
                        verified_parsed["sourceSnippets"] = snippets
                    response_text = json.dumps(verified_parsed, ensure_ascii=False)
                    verified = True
                else:
                    logger.warning(
                        "Pass 2 returned unusable JSON — keeping Pass 1 candidate."
                    )

    emit("Parsing Gemini JSON…", percent=90, title="Generating document")
    return finalize_creation(
        response_text,
        game,
        platform,
        creation_type,
        model_info={
            "provider": "gemini",
            "repo_id": model_name,
            "modality": "text",
            "temperature": temperature,
            "google_search": bool(search_used),
            "two_pass_verify": bool(verified),
        },
        grounding_sources=grounding_sources or None,
        exact_title=exact_title,
        prompt=prompt_text,
    )
