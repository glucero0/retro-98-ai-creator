"""Import / duplicate creation helpers."""

from __future__ import annotations

from retro_98_ai_creator.api import Api
from retro_98_ai_creator.creation_utils import (
    build_media_creation,
    build_text_creation_from_plain,
)
from retro_98_ai_creator.storage import ArchiveStore


def test_duplicate_text_creation(tmp_path):
    api = Api()
    api.store = ArchiveStore(path=tmp_path / "archives.json")

    original = build_text_creation_from_plain(
        "Hello body", prompt="Say hello", title="Greeting"
    )
    saved = api.store.upsert(original)
    res = api.duplicate_creation(saved["id"])
    assert res["ok"] is True
    copy = res["creation"]
    assert copy["id"] != saved["id"]
    assert "(copy)" in copy["title"]
    assert copy["modality"] == "text"
    assert "Hello body" in (copy["sections"][0]["content"] or "")


def test_build_media_import_shape():
    c = build_media_creation(
        modality="image",
        prompt="Imported from x.png",
        media_path="media/doc_abc.png",
        mime_type="image/png",
        title="x",
        creation_id="doc_abc",
    )
    assert c["modality"] == "image"
    assert c["mediaPath"] == "media/doc_abc.png"
    assert c["id"] == "doc_abc"
