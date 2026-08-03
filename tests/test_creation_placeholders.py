"""Creation description placeholders."""

from retro_98_ai_creator.presets import (
    apply_creation_placeholders,
    resolve_creation_description,
)


def test_apply_creation_placeholders():
    raw = "Controls for [GAME] on [PLATFORM]. Also [game] / [platform]."
    out = apply_creation_placeholders(raw, "Halo 3", "Xbox 360")
    assert out == "Controls for Halo 3 on Xbox 360. Also Halo 3 / Xbox 360."


def test_apply_placeholders_keeps_tokens_when_empty():
    raw = "Title [GAME] / [PLATFORM]"
    assert apply_creation_placeholders(raw, "", "") == raw
    assert apply_creation_placeholders(raw, "Doom", "") == "Title Doom / [PLATFORM]"


def test_resolve_prefers_override():
    out = resolve_creation_description(
        "Quick Reference Card",
        "Halo 3",
        "Xbox 360",
        override="Bind [GAME] on [PLATFORM]",
    )
    assert out == "Bind Halo 3 on Xbox 360"


def test_resolve_falls_back_to_catalog():
    out = resolve_creation_description(
        "Quick Reference Card",
        "Watch Dogs",
        "Sony PlayStation 4 (PS4)",
    )
    assert "Watch Dogs" in out
    assert "Sony PlayStation 4 (PS4)" in out
    assert "[GAME]" not in out
    assert "[PLATFORM]" not in out
