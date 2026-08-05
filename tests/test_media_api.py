"""API media replace / edit export / import (mocked dialogs & ffmpeg)."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from retro_98_ai_creator.api import Api
from retro_98_ai_creator.creation_utils import build_media_creation
from retro_98_ai_creator.storage import ArchiveStore


def _api_with_tmp_store(tmp_path, monkeypatch) -> Api:
    api = Api()
    api.config = {
        "paths": {"archives": str(tmp_path / "archives.json"), "media": "media"},
    }
    api.store = ArchiveStore(path=tmp_path / "archives.json")
    monkeypatch.setattr(
        "retro_98_ai_creator.media_store.PROJECT_ROOT", tmp_path
    )
    monkeypatch.setattr(
        "retro_98_ai_creator.media_store.load_config",
        lambda: api.config,
    )
    return api


def test_replace_creation_media_writes_image(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    creation = build_media_creation(
        modality="image",
        prompt="test",
        media_path="media/doc_img1.png",
        mime_type="image/png",
        title="Shot",
        creation_id="doc_img1",
    )
    api.store.upsert(creation)
    # Seed original media file path used by record (optional)
    (tmp_path / "media").mkdir(parents=True, exist_ok=True)

    png = base64.b64encode(b"\x89PNG\r\n\x1a\nedited").decode("ascii")
    res = api.replace_creation_media(
        "doc_img1",
        f"data:image/png;base64,{png}",
        "image/png",
    )
    assert res["ok"] is True
    saved = res["creation"]
    assert saved["id"] == "doc_img1"
    assert saved["modality"] == "image"
    assert saved.get("mediaPath")
    media_file = tmp_path / saved["mediaPath"]
    assert media_file.is_file()
    assert b"edited" in media_file.read_bytes()


def test_replace_creation_media_rejects_non_image(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    video = build_media_creation(
        modality="video",
        prompt="clip",
        media_path="media/doc_v1.mp4",
        mime_type="video/mp4",
        title="Clip",
        creation_id="doc_v1",
    )
    api.store.upsert(video)
    res = api.replace_creation_media("doc_v1", base64.b64encode(b"x").decode(), "image/png")
    assert res["ok"] is False
    assert "image" in (res.get("error") or "").lower()


def test_replace_creation_media_missing_id(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    assert api.replace_creation_media("", "aaaa")["ok"] is False
    assert api.replace_creation_media("missing", "aaaa")["ok"] is False


def test_edit_video_overwrites_media(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    (tmp_path / "media").mkdir(parents=True, exist_ok=True)
    src = tmp_path / "media" / "doc_vid.mp4"
    src.write_bytes(b"source-bytes")
    creation = build_media_creation(
        modality="video",
        prompt="vid",
        media_path="media/doc_vid.mp4",
        mime_type="video/mp4",
        title="Vid",
        creation_id="doc_vid",
    )
    api.store.upsert(creation)

    rendered = tmp_path / "rendered.mp4"
    rendered.write_bytes(b"edited-video-bytes")

    def fake_render(creation_id, ops=None):
        assert creation_id == "doc_vid"
        assert ops and ops.get("segments")
        return None, rendered, creation

    monkeypatch.setattr(api, "_render_edited_video", fake_render)
    res = api.edit_video(
        "doc_vid",
        {"segments": [{"start": 0, "end": 1}], "filters": {"brightness": 5}},
    )
    assert res["ok"] is True
    assert res["creation"]["id"] == "doc_vid"
    out = tmp_path / res["creation"]["mediaPath"]
    assert out.read_bytes() == b"edited-video-bytes"
    assert not rendered.exists()  # cleaned up in finally


def test_export_edited_video_save_dialog(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    creation = build_media_creation(
        modality="video",
        prompt="vid",
        media_path="media/doc_exp.mp4",
        mime_type="video/mp4",
        title="Export Me",
        creation_id="doc_exp",
    )
    api.store.upsert(creation)
    rendered = tmp_path / "rendered_export.mp4"
    rendered.write_bytes(b"export-bytes")
    dest = tmp_path / "user_save.mp4"

    monkeypatch.setattr(
        api,
        "_render_edited_video",
        lambda creation_id, ops=None: (None, rendered, creation),
    )
    win = MagicMock()
    win.create_file_dialog.return_value = str(dest)
    api._window = win

    res = api.export_edited_video(
        "doc_exp", {"segments": [{"start": 0, "end": 2}]}
    )
    assert res["ok"] is True
    assert Path(res["path"]) == dest
    assert dest.read_bytes() == b"export-bytes"


def test_export_edited_video_cancelled(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    creation = build_media_creation(
        modality="video",
        prompt="vid",
        media_path="media/doc_exp2.mp4",
        mime_type="video/mp4",
        title="Clip",
        creation_id="doc_exp2",
    )
    api.store.upsert(creation)
    rendered = tmp_path / "rendered_cancel.mp4"
    rendered.write_bytes(b"x")
    monkeypatch.setattr(
        api,
        "_render_edited_video",
        lambda creation_id, ops=None: (None, rendered, creation),
    )
    win = MagicMock()
    win.create_file_dialog.return_value = None
    api._window = win
    res = api.export_edited_video("doc_exp2", {"segments": [{"start": 0, "end": 1}]})
    assert res.get("cancelled") is True


def test_import_media_file_image(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    src = tmp_path / "photo.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\nhello")
    win = MagicMock()
    win.create_file_dialog.return_value = str(src)
    api._window = win

    res = api.import_media_file("image")
    assert res["ok"] is True
    assert res["modality"] == "image"
    c = res["creation"]
    assert c["modality"] == "image"
    assert c["title"] == "photo"
    assert "Imported from photo.png" in c["prompt"]
    media = tmp_path / c["mediaPath"]
    assert media.read_bytes().startswith(b"\x89PNG")


def test_import_media_file_cancelled(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    win = MagicMock()
    win.create_file_dialog.return_value = None
    api._window = win
    res = api.import_media_file("video")
    assert res.get("cancelled") is True


def test_import_text_file_into_prompt(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    src = tmp_path / "notes.txt"
    src.write_text("Hello studio basis", encoding="utf-8")
    win = MagicMock()
    win.create_file_dialog.return_value = str(src)
    api._window = win

    res = api.import_text_file(False)
    assert res["ok"] is True
    assert res["text"] == "Hello studio basis"
    assert "creation" not in res

    res2 = api.import_text_file(True)
    assert res2["ok"] is True
    assert res2["creation"]["modality"] == "text"
    assert "Hello studio basis" in res2["creation"]["sections"][0]["content"]


def test_duplicate_image_copies_media(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    (tmp_path / "media").mkdir(parents=True, exist_ok=True)
    src = tmp_path / "media" / "doc_dup.png"
    src.write_bytes(b"image-bytes")
    creation = build_media_creation(
        modality="image",
        prompt="orig",
        media_path="media/doc_dup.png",
        mime_type="image/png",
        title="Original",
        creation_id="doc_dup",
    )
    api.store.upsert(creation)
    res = api.duplicate_creation("doc_dup")
    assert res["ok"] is True
    copy = res["creation"]
    assert copy["id"] != "doc_dup"
    assert "(copy)" in copy["title"]
    assert (tmp_path / copy["mediaPath"]).read_bytes() == b"image-bytes"


def test_get_media_payload_image_includes_file_url(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    api._ui_origin = "http://127.0.0.1:8765"
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    img_path = media_dir / "doc_basis.png"
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    img_path.write_bytes(png)
    creation = build_media_creation(
        modality="image",
        prompt="basis",
        media_path="media/doc_basis.png",
        mime_type="image/png",
        title="Basis",
        creation_id="doc_basis",
    )
    api.store.upsert(creation)
    res = api.get_media_payload(creation)
    assert res["ok"] is True
    assert res["modality"] == "image"
    assert res.get("fileUrl") == "http://127.0.0.1:8765/media/doc_basis.png"
    assert str(res.get("dataUrl") or "").startswith("data:image/")
