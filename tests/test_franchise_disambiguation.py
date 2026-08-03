"""Tests for franchise base-name → Search Results disambiguation."""

import pytest

from retro_98_ai_creator.creation_utils import AmbiguousGameError, GameNotFoundError, finalize_creation
from retro_98_ai_creator.franchise_disambiguation import (
    find_franchise_key,
    resolve_franchise_ambiguity,
)
from retro_98_ai_creator.generator import generate_creation


def test_call_of_duty_is_ambiguous():
    hits = resolve_franchise_ambiguity("call of duty")
    assert hits is not None
    assert len(hits) >= 5
    names = [h["game"].lower() for h in hits]
    assert any("black ops" in n for n in names)
    assert any(n == "call of duty" for n in names)


def test_gibberish_is_not_a_franchise():
    assert resolve_franchise_ambiguity("blah blah x hex dietem wonder") is None
    assert find_franchise_key("blah blah x hex dietem wonder") is None


def test_specific_cod_title_skips_ambiguity():
    # Fully specific catalog title with no longer extensions → unique enough
    assert resolve_franchise_ambiguity("Call of Duty: Modern Warfare 3") is None


def test_black_ops_still_ambiguous_across_entries():
    hits = resolve_franchise_ambiguity("call of duty black ops")
    assert hits is not None
    assert len(hits) >= 2
    assert all("black ops" in h["game"].lower() for h in hits)


def test_finalize_raises_ambiguous_for_cod_even_if_model_says_not_found():
    raw = '{"game":"Game Not Found","notFound":true,"sections":[]}'
    with pytest.raises(AmbiguousGameError) as ei:
        finalize_creation(raw, "call of duty", "PC", "Manual")
    assert len(ei.value.candidates) >= 5


def test_finalize_exact_title_skips_franchise_catalog():
    # After user picks from Search Results, generate even if query string is a franchise base
    raw = """{
      "game": "Call of Duty",
      "platform": "PC",
      "creationType": "Manual",
      "overview": "ok",
      "sections": [],
      "accuracyNote": "n"
    }"""
    doc = finalize_creation(raw, "Call of Duty", "PC", "Manual", exact_title=True)
    assert doc["game"] == "Call of Duty"


def test_generate_creation_raises_before_backend_for_cod():
    with pytest.raises(AmbiguousGameError) as ei:
        generate_creation(
            "call of duty",
            "PC",
            "Manual",
            config={"backend": {"provider": "gemini"}},
            exact_title=False,
        )
    assert "call of duty" in str(ei.value).lower() or len(ei.value.candidates) >= 2


def test_generate_creation_gibberish_reaches_backend_path():
    # Without franchise hit, generator proceeds to provider (which fails without API key)
    with pytest.raises(RuntimeError, match="API key"):
        generate_creation(
            "blah blah x hex dietem wonder",
            "PC",
            "Manual",
            config={"backend": {"provider": "gemini"}, "gemini": {}},
            exact_title=False,
        )
