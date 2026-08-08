"""Tests for search-image discovery and OCR enrichment."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retro_98_ai_creator.config import DEFAULTS
from retro_98_ai_creator.research_images import (
    discover_image_urls,
    domain_allowed,
    enrich_research_with_image_ocr,
    extract_image_urls_from_html,
    extract_image_urls_from_text,
)


def test_ocr_search_images_default_is_true():
    assert DEFAULTS["gemini"]["ocr_search_images"] is True
    assert DEFAULTS["gemini"]["youtube_search_captions"] is True


def test_extract_image_urls_from_text():
    text = (
        "See https://example.com/guide.png and "
        "https://other.com/page.html for details."
    )
    urls = extract_image_urls_from_text(text)
    assert urls == ["https://example.com/guide.png"]


def test_extract_image_urls_from_html():
    html = """
    <html>
      <head>
        <meta property="og:image" content="https://example.com/og.jpg" />
      </head>
      <body>
        <img src="/assets/diagram.png" />
      </body>
    </html>
    """
    urls = extract_image_urls_from_html(
        html, base_url="https://example.com/article"
    )
    assert "https://example.com/assets/diagram.png" in urls
    assert "https://example.com/og.jpg" in urls


def test_domain_allowed_rejects_off_citation_hosts():
    allowed = {"example.com"}
    assert domain_allowed("https://example.com/img.png", allowed)
    assert domain_allowed("https://cdn.example.com/img.png", allowed)
    assert not domain_allowed("https://evil.com/img.png", allowed)


def test_discover_image_urls_filters_by_grounding_domains():
    research = "Found https://evil.com/secret.png and https://example.com/table.png"
    sources = [{"title": "Guide", "url": "https://example.com/guide"}]
    urls = discover_image_urls(research, grounding_sources=sources)
    assert urls == ["https://example.com/table.png"]


def test_enrich_research_with_image_ocr_appends_block():
    research = "Bindings at https://example.com/bindings.png"
    sources = [{"title": "IGN", "url": "https://example.com/controls"}]
    fake_png = b"\x89PNG" + (b"x" * 3000)

    with (
        patch(
            "retro_98_ai_creator.research_images.discover_image_urls",
            return_value=["https://example.com/bindings.png"],
        ),
        patch(
            "retro_98_ai_creator.research_images.download_image",
            return_value=(fake_png, "image/png"),
        ),
        patch(
            "retro_98_ai_creator.research_images.ocr_image_bytes",
            return_value=("Square = Jump", "gemini-2.5-flash"),
        ),
    ):
        block, meta = enrich_research_with_image_ocr(
            research,
            grounding_sources=sources,
            config={"backend": {"provider": "gemini"}, "gemini": {}},
        )

    assert "IMAGE OCR FINDINGS" in block
    assert "https://example.com/bindings.png" in block
    assert "Square = Jump" in block
    assert meta["ocrImageCount"] == 1
    assert meta["ocrImageUrls"] == ["https://example.com/bindings.png"]


def test_enrich_skips_no_text_results():
    research = "See https://example.com/icon.png"
    sources = [{"title": "Page", "url": "https://example.com/page"}]
    fake_png = b"\x89PNG" + (b"x" * 3000)

    with (
        patch(
            "retro_98_ai_creator.research_images.discover_image_urls",
            return_value=["https://example.com/icon.png"],
        ),
        patch(
            "retro_98_ai_creator.research_images.download_image",
            return_value=(fake_png, "image/png"),
        ),
        patch(
            "retro_98_ai_creator.research_images.ocr_image_bytes",
            return_value=("(no text found)", "gemini-2.5-flash"),
        ),
    ):
        block, meta = enrich_research_with_image_ocr(
            research,
            grounding_sources=sources,
            config={"backend": {"provider": "gemini"}, "gemini": {}},
        )

    assert block == ""
    assert meta["ocrImageCount"] == 0


def test_tools_pipeline_includes_ocr_block_in_research_context():
    """Research pass enrichment injects OCR text into the tool-loop prompt."""
    from types import SimpleNamespace

    from retro_98_ai_creator import gemini_provider as gp

    research = SimpleNamespace(
        text="Research with https://example.com/table.png",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(
                            function_call=None,
                            text="Research with https://example.com/table.png",
                        )
                    ]
                ),
                grounding_metadata=SimpleNamespace(
                    grounding_chunks=[
                        SimpleNamespace(
                            web=SimpleNamespace(
                                title="Guide",
                                uri="https://example.com/guide",
                            )
                        )
                    ],
                    search_entry_point=None,
                    web_search_queries=["controls"],
                ),
            )
        ],
    )
    final = SimpleNamespace(
        text="Wrote output.",
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[SimpleNamespace(function_call=None, text="Wrote output.")]
                ),
                grounding_metadata=None,
            )
        ],
    )

    client = MagicMock()
    tool_prompts: list[str] = []

    def _side_effect(**kwargs):
        contents = kwargs.get("contents")
        if isinstance(contents, str):
            return research
        if contents:
            tool_prompts.append(contents[0].parts[0].text)
        return final

    client.models.generate_content.side_effect = _side_effect

    ocr_block = (
        "IMAGE OCR FINDINGS (from search sources):\n"
        "- https://example.com/table.png\n"
        "  A = Jump\n"
    )

    with (
        patch.object(gp, "resolve_api_key", return_value="fake-key"),
        patch("google.genai.Client", return_value=client),
        patch(
            "retro_98_ai_creator.search_enrichment.apply_search_enrichment",
            return_value=(
                "Research with https://example.com/table.png\n\n" + ocr_block,
                ocr_block,
                {"ocrImageCount": 1, "ocrImageUrls": ["https://example.com/table.png"]},
            ),
        ),
    ):
        result = gp._generate_text_with_gemini(
            "Prompt",
            "General",
            "Custom",
            gemini_cfg={
                "api_key": "fake-key",
                "use_tools": True,
                "google_search": True,
                "ocr_search_images": True,
                "temperature": 0.0,
            },
            prompt_text="use write_json to save c:\\out\\bindings.json",
            model_name="gemini-pro-latest",
            tool_aliases=["write_json"],
            search_query="Watch Dogs PS4 controls",
        )

    assert tool_prompts
    assert "IMAGE OCR FINDINGS" in tool_prompts[0]
    assert "A = Jump" in tool_prompts[0]
    assert (result.get("_model") or {}).get("ocrImageCount") == 1
