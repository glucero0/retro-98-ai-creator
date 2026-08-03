"""Platform catalog and hardware prompt block."""

from retro_98_ai_creator.presets import (
    PLATFORM_OPTIONS,
    PLATFORMS,
    platform_button_labels,
    platform_for,
)
from retro_98_ai_creator.prompts import _platform_hardware_block


def test_platforms_catalog_loaded():
    assert len(PLATFORMS) >= 5
    assert len(PLATFORM_OPTIONS) == len(PLATFORMS)
    for entry in PLATFORMS:
        assert entry["id"]
        assert entry["label"]
        assert isinstance(entry.get("controllers"), list)


def test_platform_for_id_and_label():
    by_id = platform_for("apple-ii")
    assert by_id is not None
    assert by_id["label"] == "Apple II / IIe"
    by_label = platform_for(by_id["label"])
    assert by_label is not None
    assert by_label["id"] == "apple-ii"
    assert platform_for("") is None
    assert platform_for("not-a-real-platform") is None


def test_platform_button_labels_include_controllers():
    labels = platform_button_labels("apple-ii")
    assert "Space" in labels or "Open Apple" in labels
    assert any(labels)


def test_platform_hardware_block_embeds_catalog():
    block = _platform_hardware_block("Apple II / IIe")
    assert "PLATFORM HARDWARE" in block
    assert "Open Apple" in block or "Keyboard" in block
    assert _platform_hardware_block("") == ""
    assert _platform_hardware_block("Unknown Console XYZ") == ""
