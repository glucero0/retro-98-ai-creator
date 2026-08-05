"""OpenRouter model listing helpers."""

from retro_98_ai_creator.openrouter_provider import (
    OPENROUTER_LIST_LIMIT,
    SUGGESTED_OPENROUTER_MODELS,
    _modality_from_openrouter_item,
    _openrouter_model_label,
    list_available_openrouter_models,
    merge_openrouter_model_suggestions,
)


def test_openrouter_model_label():
    assert _openrouter_model_label("google/gemini-2.5-flash", "Gemini 2.5 Flash") == (
        "Gemini 2.5 Flash"
    )
    assert _openrouter_model_label("openai/gpt-4o", None) == "gpt-4o"
    assert (
        _openrouter_model_label(
            "nvidia/nemotron",
            "NVIDIA: Nemotron 3 Ultra (free) — NVIDIA Nemotron 3 Ultra is an open "
            "frontier-reasoning model that goes on forever",
        )
        == "NVIDIA: Nemotron 3 Ultra (free)"
    )


def test_modality_from_openrouter_item():
    assert (
        _modality_from_openrouter_item(
            {
                "id": "alibaba/wan-2.7",
                "architecture": {"output_modalities": ["video"]},
            },
            "video",
        )
        == "video"
    )
    assert (
        _modality_from_openrouter_item(
            {
                "id": "black-forest-labs/flux.2-pro",
                "architecture": {"output_modalities": ["image"]},
            },
            "image",
        )
        == "image"
    )
    assert (
        _modality_from_openrouter_item(
            {
                "id": "deepseek/deepseek-chat",
                "architecture": {"output_modalities": ["text"]},
            },
            "text",
        )
        == "text"
    )
    assert (
        _modality_from_openrouter_item(
            {
                "id": "openai/text-embedding-3-large",
                "architecture": {"output_modalities": ["embeddings"]},
            },
            "text",
        )
        is None
    )


def test_merge_openrouter_model_suggestions():
    live = [
        {
            "repo_id": "org/live-text",
            "label": "live",
            "notes": "popular",
            "modality": "text",
        }
    ]
    curated = [
        {
            "repo_id": "org/live-text",
            "label": "dup",
            "notes": "curated",
            "modality": "text",
        },
        {
            "repo_id": "google/gemini-2.5-flash",
            "label": "Flash",
            "notes": "curated",
            "modality": "text",
        },
    ]
    merged = merge_openrouter_model_suggestions(live, curated)
    assert merged[0]["label"] == "live"
    assert any(m["repo_id"] == "google/gemini-2.5-flash" for m in merged)


def test_list_available_openrouter_models_mocked(monkeypatch):
    calls: list[str] = []

    def fake_fetch(*, output_modality, sort="most-popular", api_key=None, base_url=""):
        calls.append(output_modality)
        assert sort == "most-popular"
        if output_modality == "text":
            return [
                {
                    "id": "org/a-text",
                    "name": "A Text",
                    "description": "A solid chat model",
                    "architecture": {"output_modalities": ["text"]},
                },
                {
                    "id": "org/b-text",
                    "name": "B Text",
                    "architecture": {"output_modalities": ["text"]},
                },
            ]
        if output_modality == "image":
            return [
                {
                    "id": "org/a-image",
                    "name": "A Image",
                    "architecture": {"output_modalities": ["image"]},
                }
            ]
        if output_modality == "video":
            return [
                {
                    "id": "org/a-video",
                    "name": "A Video",
                    "architecture": {"output_modalities": ["video"]},
                }
            ]
        return []

    monkeypatch.setattr(
        "retro_98_ai_creator.openrouter_provider._fetch_openrouter_models",
        fake_fetch,
    )
    models = list_available_openrouter_models({}, limit=OPENROUTER_LIST_LIMIT)
    assert calls == ["text", "image", "video"]
    by_mod = {}
    for m in models:
        by_mod.setdefault(m["modality"], []).append(m["repo_id"])
    assert by_mod["text"] == ["org/a-text", "org/b-text"]
    assert by_mod["image"] == ["org/a-image"]
    assert by_mod["video"] == ["org/a-video"]
    assert models[0]["label"] == "A Text"


def test_suggested_openrouter_models_have_modalities():
    mods = {m.get("modality") for m in SUGGESTED_OPENROUTER_MODELS}
    assert {"text", "image", "video"} <= mods
