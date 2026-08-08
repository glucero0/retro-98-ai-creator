"""Tests for YouTube caption enrichment from search."""

from __future__ import annotations

from unittest.mock import patch

from retro_98_ai_creator.config import DEFAULTS
from retro_98_ai_creator.research_youtube import (
    discover_youtube_urls,
    enrich_research_with_youtube_captions,
    extract_youtube_video_id,
    is_youtube_url,
)


def test_youtube_search_captions_default_is_true():
    assert DEFAULTS["gemini"]["youtube_search_captions"] is True


def test_extract_youtube_video_id_watch():
    assert (
        extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        == "dQw4w9WgXcQ"
    )


def test_extract_youtube_video_id_short_link():
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_discover_youtube_urls_from_grounding():
    sources = [{"title": "Guide", "url": "https://www.youtube.com/watch?v=abc123XYZ12"}]
    urls = discover_youtube_urls("See also https://youtu.be/def456UVW78", grounding_sources=sources)
    assert len(urls) == 2
    assert all(is_youtube_url(u) for u in urls)


def test_enrich_research_with_youtube_captions_appends_block():
    sources = [{"title": "Controls", "url": "https://www.youtube.com/watch?v=abc123XYZ12"}]

    with patch(
        "retro_98_ai_creator.research_youtube._fetch_captions",
        return_value="Press R1 to sprint.",
    ):
        block, meta = enrich_research_with_youtube_captions(
            "Video walkthrough",
            grounding_sources=sources,
        )

    assert "YOUTUBE CAPTION FINDINGS" in block
    assert "Press R1 to sprint." in block
    assert meta["youtubeCaptionCount"] == 1
