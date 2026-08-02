"""Tests for JSON extraction / repair used after local LLM generation."""

import pytest

from game_base_ref_creator.creation_utils import (
    AmbiguousGameError,
    GameNotFoundError,
    extract_json_object,
    finalize_creation,
    is_ambiguous,
    is_game_not_found,
    normalize_candidates,
)
from game_base_ref_creator.prompts import build_prompt


def test_extract_plain_json():
    raw = '{"game": "Doom", "platform": "MS-DOS", "sections": []}'
    data = extract_json_object(raw)
    assert data["game"] == "Doom"


def test_extract_markdown_fenced():
    raw = """```json
{"game": "Halo", "platform": "Xbox", "overview": "ok"}
```"""
    data = extract_json_object(raw)
    assert data["game"] == "Halo"


def test_extract_with_preamble():
    raw = 'Here is the document:\n{"game": "Pitfall!", "platform": "Atari 2600", "x": 1}\nThanks'
    data = extract_json_object(raw)
    assert data["game"] == "Pitfall!"


def test_truncated_json_repair():
    raw = '{"game": "Sonic", "platform": "Genesis", "sections": [{"title": "Cheats"'
    data = extract_json_object(raw)
    assert data is not None
    assert data["game"] == "Sonic"


def test_finalize_strips_section_icon():
    raw = """{
      "game": "Pitfall!",
      "platform": "Atari 2600",
      "creationType": "Manual",
      "overview": "ok",
      "sections": [{"title": "A", "icon": "info", "content": "x", "keyValues": []}],
      "accuracyNote": "n"
    }"""
    doc = finalize_creation(raw, "Pitfall!", "Atari 2600", "Manual")
    assert "icon" not in doc["sections"][0]
    assert doc["createdAt"]
    assert doc["id"]


def test_finalize_prefers_model_canonical_game_name():
    raw = """{
      "game": "Final Fantasy VII",
      "platform": "Sony PlayStation (PS1)",
      "creationType": "Manual",
      "overview": "ok",
      "sections": [],
      "accuracyNote": "n"
    }"""
    # Typo of a specific entry — exact_title False but not a bare franchise stem with residual?
    # "final fantacy 7" is not a franchise key match for bare "final fantasy"
    doc = finalize_creation(raw, "final fantacy 7", "Sony PlayStation (PS1)", "Manual")
    assert doc["game"] == "Final Fantasy VII"
    assert doc["_userGame"] == "final fantacy 7"


def test_is_game_not_found_flag():
    assert is_game_not_found({"game": "Hexen", "notFound": True})
    assert is_game_not_found({"game": "Game Not Found"})
    assert not is_game_not_found({"game": "Doom", "notFound": False})


def test_finalize_raises_on_game_not_found():
    raw = """{
      "game": "Game Not Found",
      "notFound": true,
      "platform": "MS-DOS",
      "creationType": "Manual",
      "overview": "No match",
      "sections": []
    }"""
    with pytest.raises(GameNotFoundError, match="Game Not Found"):
        finalize_creation(raw, "blah blah x hex dietem wonder", "MS-DOS", "Manual")


def test_normalize_candidates_dedupes_and_accepts_strings():
    raw = [
        {"game": "Call of Duty", "year": "2003", "note": "Original"},
        {"game": "Call of Duty", "year": "2003"},
        "Call of Duty: Black Ops",
        {"title": "Call of Duty 2", "releaseYear": "2005"},
        {"game": ""},
    ]
    out = normalize_candidates(raw)
    assert [c["game"] for c in out] == [
        "Call of Duty",
        "Call of Duty: Black Ops",
        "Call of Duty 2",
    ]
    assert out[0]["year"] == "2003"
    assert out[0]["note"] == "Original"


def test_is_ambiguous_requires_multiple_candidates():
    assert not is_ambiguous({"ambiguous": True, "candidates": [{"game": "Only One"}]})
    assert is_ambiguous(
        {
            "ambiguous": True,
            "candidates": [
                {"game": "Call of Duty"},
                {"game": "Call of Duty: Black Ops"},
            ],
        }
    )
    # Candidates win over notFound when both are present
    assert is_ambiguous(
        {
            "notFound": True,
            "ambiguous": True,
            "candidates": [{"game": "A"}, {"game": "B"}],
        }
    )


def test_finalize_raises_on_ambiguous():
    raw = """{
      "game": "Ambiguous",
      "ambiguous": true,
      "platform": "PC",
      "creationType": "Manual",
      "candidates": [
        {"game": "Some Indie Game A", "year": "2001", "note": "One"},
        {"game": "Some Indie Game B", "year": "2002", "note": "Two"}
      ],
      "sections": []
    }"""
    with pytest.raises(AmbiguousGameError) as ei:
        finalize_creation(raw, "some indie game", "PC", "Manual")
    assert ei.value.user_game == "some indie game"
    assert len(ei.value.candidates) == 2
    assert ei.value.candidates[0]["game"] == "Some Indie Game A"


def test_exact_title_prompt_skips_ambiguous_schema():
    prompt = build_prompt("Call of Duty", "PC", "Manual", exact_title=True)
    assert "CONFIRMED TITLE" in prompt
    assert "already chosen" in prompt
    assert '"ambiguous": true' not in prompt
    assert "candidates" not in prompt.lower()


def test_disambiguation_prompt_includes_ambiguous_schema():
    prompt = build_prompt("call of duty", "PC", "Manual", exact_title=False)
    assert "DISAMBIGUATION" in prompt
    assert '"ambiguous": true' in prompt
    assert "candidates" in prompt
