"""Shared helpers for turning raw model text into a GameCreation document."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .fallbacks import build_emergency_creation, get_dynamic_fallback_meta


class GameNotFoundError(RuntimeError):
    """Raised when the model (correctly) reports the game cannot be identified."""

    def __init__(self, user_game: str = "") -> None:
        self.user_game = (user_game or "").strip()
        msg = "Game Not Found"
        if self.user_game:
            msg = f'Game Not Found — no confident match for "{self.user_game}".'
        super().__init__(msg)


class AmbiguousGameError(RuntimeError):
    """Raised when multiple real titles match the user query."""

    def __init__(
        self,
        user_game: str = "",
        candidates: list[dict[str, str]] | None = None,
    ) -> None:
        self.user_game = (user_game or "").strip()
        self.candidates = list(candidates or [])
        n = len(self.candidates)
        msg = f"Ambiguous game title — {n} match{'es' if n != 1 else ''}."
        if self.user_game:
            msg = f'Ambiguous — {n} matches for "{self.user_game}".'
        super().__init__(msg)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_game_not_found(parsed: dict[str, Any] | None) -> bool:
    """True when model output indicates the title could not be identified."""
    if not isinstance(parsed, dict):
        return False
    if parsed.get("notFound") is True:
        return True
    game = str(parsed.get("game") or "").strip().lower()
    return game in {"game not found", "not found", "unknown game"}


def normalize_candidates(raw: Any) -> list[dict[str, str]]:
    """Normalize model candidate list into [{game, year, platform, note}, ...]."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            name = item.strip()
            year = platform = note = ""
        elif isinstance(item, dict):
            name = str(item.get("game") or item.get("title") or item.get("name") or "").strip()
            year = str(item.get("year") or item.get("releaseYear") or "").strip()
            platform = str(item.get("platform") or "").strip()
            note = str(item.get("note") or item.get("subtitle") or item.get("desc") or "").strip()
        else:
            continue
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append({"game": name, "year": year, "platform": platform, "note": note})
    return out


def is_ambiguous(parsed: dict[str, Any] | None) -> bool:
    """True when model output indicates multiple matching titles."""
    if not isinstance(parsed, dict):
        return False
    candidates = normalize_candidates(parsed.get("candidates"))
    if len(candidates) < 2:
        return False
    # Prefer Search Results over Not Found when the model also listed candidates
    if parsed.get("ambiguous") is True:
        return True
    if str(parsed.get("game") or "").strip().lower() in {
        "ambiguous",
        "multiple matches",
        "search results",
    }:
        return True
    return False


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
    exact_title: bool = False,
) -> dict[str, Any]:
    """Parse model JSON (or emergency fallback) and attach ids / metadata.

    Raises GameNotFoundError when the model reports the title is unrecognized.
    Raises AmbiguousGameError when multiple titles match the query.
    """
    # Known franchise base names → Search Results (do not trust model notFound here)
    if not exact_title:
        from .franchise_disambiguation import resolve_franchise_ambiguity

        franchise_hits = resolve_franchise_ambiguity(game)
        if franchise_hits and len(franchise_hits) >= 2:
            raise AmbiguousGameError(game, franchise_hits)

    parsed = extract_json_object(text)
    if is_ambiguous(parsed):
        raise AmbiguousGameError(game, normalize_candidates(parsed.get("candidates")))
    if is_game_not_found(parsed):
        raise GameNotFoundError(game)

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
        parsed.pop("notFound", None)
        parsed.pop("ambiguous", None)
        parsed.pop("candidates", None)
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
