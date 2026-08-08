"""Post-search enrichment: image OCR and YouTube captions."""

from __future__ import annotations

from typing import Any, Callable

ProgressCallback = Callable[[Any], None]


def apply_search_enrichment(
    text: str,
    *,
    grounding_sources: list[dict[str, str]] | None,
    gemini_cfg: dict[str, Any],
    progress: ProgressCallback | None = None,
    cancel_event: Any = None,
) -> tuple[str, str, dict[str, Any]]:
    """
    Run enabled search enrichments on research/search text.

    Returns (enriched_text, appended_blocks_only, meta).
    """
    config = {"backend": {"provider": "gemini"}, "gemini": gemini_cfg or {}}
    base = (text or "").strip()
    blocks: list[str] = []
    meta: dict[str, Any] = {}

    if not grounding_sources:
        return base, "", meta

    if bool(gemini_cfg.get("ocr_search_images", True)):
        from .research_images import enrich_research_with_image_ocr

        block, ocr_meta = enrich_research_with_image_ocr(
            base,
            grounding_sources=grounding_sources,
            config=config,
            progress=progress,
            cancel_event=cancel_event,
        )
        meta.update(ocr_meta)
        if block:
            blocks.append(block.strip())

    if bool(gemini_cfg.get("youtube_search_captions", True)):
        from .research_youtube import enrich_research_with_youtube_captions

        block, yt_meta = enrich_research_with_youtube_captions(
            base,
            grounding_sources=grounding_sources,
            progress=progress,
            cancel_event=cancel_event,
        )
        for key, value in yt_meta.items():
            if key not in meta or value:
                meta[key] = value
        if block:
            blocks.append(block.strip())

    appended = "\n\n".join(blocks)
    if not appended:
        return base, "", meta
    enriched = (base + "\n\n" + appended).strip() if base else appended
    return enriched, appended, meta
