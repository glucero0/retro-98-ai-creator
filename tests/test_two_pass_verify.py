"""Two-pass Gemini search/verify helpers and prompts."""

from retro_98_ai_creator.creation_utils import finalize_creation, normalize_source_snippets
from retro_98_ai_creator.gemini_provider import _two_pass_enabled
from retro_98_ai_creator.prompts import (
    build_search_extract_prompt,
    build_verification_prompt,
)


def test_normalize_source_snippets_dedupes_and_maps_aliases():
    raw = [
        {"source": "Wiki", "quote": "Press A to jump"},
        {"title": "Wiki", "text": "Press A to jump"},  # duplicate
        {"url": "https://example.com", "snippet": "Press B to shoot"},
        {"quote": ""},
        "ignore-me",
    ]
    out = normalize_source_snippets(raw)
    assert out == [
        {"source": "Wiki", "quote": "Press A to jump"},
        {"source": "https://example.com", "quote": "Press B to shoot"},
    ]


def test_finalize_creation_keeps_source_snippets():
    raw = """
    {
      "game": "Doom",
      "platform": "MS-DOS",
      "creationType": "Quick Reference Card",
      "overview": "FPS classic.",
      "sections": [],
      "meta": {"releaseYear": "1993"},
      "theme": {"themeName": "Doom"},
      "sourceSnippets": [
        {"source": "Manual", "quote": "Arrow keys move"}
      ]
    }
    """
    doc = finalize_creation(
        raw, "Doom", "MS-DOS", "Quick Reference Card", exact_title=True
    )
    assert doc["sourceSnippets"] == [{"source": "Manual", "quote": "Arrow keys move"}]


def test_search_extract_prompt_requires_snippets():
    prompt = build_search_extract_prompt(
        "Halo 3",
        "Xbox 360",
        "Quick Reference Card",
        creation_description="Extract controls.",
    )
    assert "PASS 1: SEARCH & EXTRACT" in prompt
    assert "sourceSnippets" in prompt
    assert "Xbox 360" in prompt


def test_verification_prompt_reviews_against_snippets():
    candidate = {
        "game": "Halo 3",
        "platform": "Xbox 360",
        "creationType": "Quick Reference Card",
        "sections": [
            {
                "title": "Controls",
                "keyValues": [{"label": "A", "value": "Jump"}],
            }
        ],
        "sourceSnippets": [{"source": "Guide", "quote": "A button = Jump"}],
    }
    prompt = build_verification_prompt(
        "Halo 3",
        "Xbox 360",
        "Quick Reference Card",
        candidate_document=candidate,
        source_snippets=[{"source": "Guide", "quote": "A button = Jump"}],
    )
    assert "PASS 2: VERIFICATION" in prompt
    assert 'mark "Unverified"' in prompt or "mark 'Unverified'" in prompt or "Unverified" in prompt
    assert "Strip out any assumed information" in prompt or "assumed information" in prompt
    assert "A button = Jump" in prompt
    assert "Quick Reference Card" in prompt


def test_two_pass_enabled_defaults():
    assert _two_pass_enabled({}, use_search=True) is True
    assert _two_pass_enabled({"two_pass_verify": False}, use_search=True) is False
    assert _two_pass_enabled({"two_pass_verify": True}, use_search=False) is False
