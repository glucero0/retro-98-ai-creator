"""Named prompt library used by Prompt Editor / Creation Studio."""

from __future__ import annotations

import json

import pytest

from retro_98_ai_creator.api import Api
from retro_98_ai_creator.storage import PromptStore


def test_prompt_store_upsert_and_list(tmp_path):
    store = PromptStore(path=tmp_path / "prompts.json")
    assert store.load() == []

    saved = store.upsert({"name": "  Cinematic  ", "body": "rim light, 35mm"})
    assert saved["id"].startswith("prm_")
    assert saved["name"] == "Cinematic"
    assert saved["body"] == "rim light, 35mm"

    items = store.load()
    assert len(items) == 1
    assert items[0]["id"] == saved["id"]

    updated = store.upsert(
        {"id": saved["id"], "name": "Cinematic", "body": "soft fill"}
    )
    assert updated["id"] == saved["id"]
    assert store.load()[0]["body"] == "soft fill"


def test_prompt_store_requires_name(tmp_path):
    store = PromptStore(path=tmp_path / "prompts.json")
    with pytest.raises(ValueError, match="name"):
        store.upsert({"name": "  ", "body": "x"})


def test_prompt_store_sorts_by_name(tmp_path):
    store = PromptStore(path=tmp_path / "prompts.json")
    store.upsert({"name": "Zebra", "body": "z"})
    store.upsert({"name": "alpha", "body": "a"})
    names = [p["name"] for p in store.load()]
    assert names == ["alpha", "Zebra"]


def test_api_save_and_list_prompts(tmp_path):
    api = Api()
    api.prompt_store = PromptStore(path=tmp_path / "prompts.json")

    empty = api.list_prompts()
    assert empty["ok"] is True
    assert empty["prompts"] == []

    missing = api.save_prompt({"name": "", "body": "nope"})
    assert missing["ok"] is False

    res = api.save_prompt({"name": "Logo style", "body": "flat vector icon"})
    assert res["ok"] is True
    assert res["prompt"]["name"] == "Logo style"
    listed = api.list_prompts()["prompts"]
    assert len(listed) == 1
    assert listed[0]["body"] == "flat vector icon"

    again = api.save_prompt(
        {
            "id": res["prompt"]["id"],
            "name": "Logo style",
            "body": "flat vector icon, white background",
        }
    )
    assert again["ok"] is True
    assert again["prompts"][0]["body"].endswith("white background")

    raw = json.loads((tmp_path / "prompts.json").read_text(encoding="utf-8"))
    assert raw[0]["name"] == "Logo style"


def test_api_delete_prompt(tmp_path):
    api = Api()
    api.prompt_store = PromptStore(path=tmp_path / "prompts.json")
    saved = api.save_prompt({"name": "Keep", "body": "a"})
    extra = api.save_prompt({"name": "Drop", "body": "b"})
    assert extra["ok"] is True

    missing = api.delete_prompt("")
    assert missing["ok"] is False

    gone = api.delete_prompt(extra["prompt"]["id"])
    assert gone["ok"] is True
    names = [p["name"] for p in gone["prompts"]]
    assert names == ["Keep"]
    assert saved["prompt"]["id"] == gone["prompts"][0]["id"]

    still = api.list_prompts()["prompts"]
    assert [p["name"] for p in still] == ["Keep"]


def test_get_bootstrap_includes_prompts(tmp_path):
    api = Api()
    api.prompt_store = PromptStore(path=tmp_path / "prompts.json")
    api.prompt_store.upsert({"name": "Hook", "body": "start with a hook"})
    boot = api.get_bootstrap()
    names = [p.get("name") for p in boot.get("prompts") or []]
    assert "Hook" in names
