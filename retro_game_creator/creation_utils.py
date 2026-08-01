"""Shared helpers for turning raw model text into a GameCreation document."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .fallbacks import build_emergency_creation, get_dynamic_fallback_meta


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Parse model output into a JSON object with multi-stage recovery."""
    clean = text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean).strip()

    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", clean)
    if match:
        candidate = match.group(0)
    else:
        start = clean.find("{")
        candidate = clean[start:] if start >= 0 else ""

    if candidate:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            repaired = _try_repair_truncated_json(candidate)
            if repaired:
                try:
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    pass
    return None


def _try_repair_truncated_json(text: str) -> str | None:
    """Best-effort close of truncated JSON objects/arrays/strings."""
    if "{" not in text:
        return None
    s = text.rstrip()
    s = re.sub(r",\s*$", "", s)

    in_string = False
    escape = False
    stack: list[str] = []
    for ch in s:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()

    if in_string:
        s += '"'
    while stack:
        s += stack.pop()
    return s


def finalize_creation(
    text: str,
    game: str,
    platform: str,
    creation_type: str,
    *,
    model_info: dict[str, Any] | None = None,
    grounding_sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Parse model JSON (or emergency fallback) and attach ids / metadata."""
    parsed = extract_json_object(text)
    if not parsed or not isinstance(parsed.get("game"), str) or not parsed.get("game", "").strip():
        parsed = build_emergency_creation(game, platform, creation_type)
    else:
        # Prefer the model's canonical title; only fall back to user input if missing
        canonical_game = str(parsed.get("game") or "").strip()
        parsed["game"] = canonical_game or game.strip()
        parsed.setdefault("platform", platform)
        parsed.setdefault("creationType", creation_type)
        parsed.setdefault("sections", [])
        parsed.setdefault("overview", "")
        parsed.setdefault("accuracyNote", "")
        if "meta" not in parsed or not isinstance(parsed["meta"], dict):
            parsed["meta"] = get_dynamic_fallback_meta(parsed["game"], platform)
        if "theme" not in parsed or not isinstance(parsed["theme"], dict):
            parsed["theme"] = {
                "themeName": f"{parsed['game']} Reference",
                "bgColor": "#008080",
                "cardBg": "#c0c0c0",
                "textColor": "#000000",
                "accentColor": "#000080",
                "headerBg": "#000080",
                "fontStyle": "retro-sans",
                "boxArtStyle": "Period authentic",
            }

    # Keep a clean display title even on emergency fallback
    if isinstance(parsed.get("game"), str):
        parsed["game"] = parsed["game"].strip()
    parsed["_userGame"] = game.strip()

    if grounding_sources:
        parsed["groundingSources"] = grounding_sources

    # Drop unused / retired section fields from model output
    cleaned_sections: list[Any] = []
    for sec in parsed.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        sec = dict(sec)
        sec.pop("icon", None)
        cleaned_sections.append(sec)
    parsed["sections"] = cleaned_sections

    parsed["id"] = f"doc_{uuid.uuid4().hex[:10]}"
    parsed["createdAt"] = _now_iso()
    if model_info:
        parsed["_model"] = model_info
    return parsed
