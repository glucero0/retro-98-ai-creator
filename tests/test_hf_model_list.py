"""Hugging Face Hub model listing helpers."""

from retro_98_ai_creator.config import SUGGESTED_MODELS
from retro_98_ai_creator.hf_provider import (
    HF_LIST_LIMIT,
    _format_download_count,
    _hf_model_label,
    list_available_hf_models,
    merge_hf_model_suggestions,
)


def test_format_download_count():
    assert _format_download_count(2_500_000) == "2.5M downloads"
    assert _format_download_count(12_400) == "12.4k downloads"
    assert _format_download_count(42) == "42 downloads"
    assert _format_download_count(0) == ""


def test_hf_model_label():
    assert _hf_model_label("stabilityai/sd-turbo") == "sd-turbo"
    assert _hf_model_label("phi-mini") == "phi-mini"


def test_merge_hf_model_suggestions_prefers_live():
    live = [
        {
            "repo_id": "org/live-text",
            "label": "live-text",
            "notes": "1.0M downloads",
            "modality": "text",
        }
    ]
    curated = [
        {
            "repo_id": "org/live-text",
            "label": "curated-dup",
            "notes": "curated",
            "modality": "text",
        },
        {
            "repo_id": "microsoft/Phi-3.5-mini-instruct",
            "label": "Phi",
            "notes": "curated",
            "modality": "text",
        },
    ]
    merged = merge_hf_model_suggestions(live, curated)
    assert merged[0]["repo_id"] == "org/live-text"
    assert merged[0]["label"] == "live-text"
    assert any(m["repo_id"] == "microsoft/Phi-3.5-mini-instruct" for m in merged)
    assert sum(1 for m in merged if m["repo_id"] == "org/live-text") == 1


def test_list_available_hf_models_mocked(monkeypatch):
    calls: list[str] = []

    def fake_fetch(pipeline_tag, *, limit, token):
        calls.append(pipeline_tag)
        assert limit == HF_LIST_LIMIT
        assert token == "hf_test"
        if pipeline_tag == "text-generation":
            return [
                {"id": "org/a-text", "downloads": 9_000_000, "likes": 100},
                {"id": "org/b-text", "downloads": 8_000_000, "likes": 50},
            ]
        if pipeline_tag == "text-to-image":
            return [{"id": "org/a-image", "downloads": 1_000_000, "likes": 10}]
        if pipeline_tag == "text-to-video":
            return [{"id": "org/a-video", "downloads": 500_000, "likes": 5}]
        return []

    monkeypatch.setattr(
        "retro_98_ai_creator.hf_provider._fetch_hub_pipeline_models",
        fake_fetch,
    )
    models = list_available_hf_models({"hf_token": "hf_test"}, limit=HF_LIST_LIMIT)
    assert calls == ["text-generation", "text-to-image", "text-to-video"]
    by_mod = {}
    for m in models:
        by_mod.setdefault(m["modality"], []).append(m["repo_id"])
    assert by_mod["text"] == ["org/a-text", "org/b-text"]
    assert by_mod["image"] == ["org/a-image"]
    assert by_mod["video"] == ["org/a-video"]
    assert "9.0M downloads" in models[0]["notes"]


def test_suggested_models_have_modalities():
    mods = {m.get("modality") for m in SUGGESTED_MODELS}
    assert {"text", "image", "video"} <= mods
