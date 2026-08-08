"""Tests for combined search enrichment orchestration."""

from __future__ import annotations

from unittest.mock import patch

from retro_98_ai_creator.search_enrichment import apply_search_enrichment


def test_apply_search_enrichment_combines_blocks():
    sources = [{"title": "Guide", "url": "https://example.com/guide"}]

    with (
        patch(
            "retro_98_ai_creator.research_images.enrich_research_with_image_ocr",
            return_value=("IMAGE OCR FINDINGS:\n- img\n  text", {"ocrImageCount": 1}),
        ),
        patch(
            "retro_98_ai_creator.research_youtube.enrich_research_with_youtube_captions",
            return_value=(
                "YOUTUBE CAPTION FINDINGS:\n- vid\n  captions",
                {"youtubeCaptionCount": 1},
            ),
        ),
    ):
        enriched, appended, meta = apply_search_enrichment(
            "research text",
            grounding_sources=sources,
            gemini_cfg={"ocr_search_images": True, "youtube_search_captions": True},
        )

    assert "IMAGE OCR FINDINGS" in appended
    assert "YOUTUBE CAPTION FINDINGS" in appended
    assert enriched.startswith("research text")
    assert meta["ocrImageCount"] == 1
    assert meta["youtubeCaptionCount"] == 1


def test_apply_search_enrichment_skips_when_disabled():
    sources = [{"title": "Guide", "url": "https://example.com/guide"}]
    enriched, appended, meta = apply_search_enrichment(
        "research text",
        grounding_sources=sources,
        gemini_cfg={"ocr_search_images": False, "youtube_search_captions": False},
    )
    assert enriched == "research text"
    assert appended == ""
    assert meta == {}
