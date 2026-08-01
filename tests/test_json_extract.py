"""Tests for JSON extraction / repair used after local LLM generation."""

from retro_game_creator.creation_utils import extract_json_object, finalize_creation


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
      "game": "Doom",
      "platform": "MS-DOS",
      "creationType": "Manual",
      "overview": "ok",
      "sections": [{"title": "A", "icon": "info", "content": "x", "keyValues": []}],
      "accuracyNote": "n"
    }"""
    doc = finalize_creation(raw, "Doom", "MS-DOS", "Manual")
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
    doc = finalize_creation(raw, "final fantacy 7", "Sony PlayStation (PS1)", "Manual")
    assert doc["game"] == "Final Fantasy VII"
    assert doc["_userGame"] == "final fantacy 7"
