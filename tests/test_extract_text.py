"""Tests for Viewer Extract Text (OCR / transcription) helpers and API."""

from __future__ import annotations

import base64
import threading

import pytest

from retro_98_ai_creator.api import Api
from retro_98_ai_creator.creation_utils import build_media_creation
from retro_98_ai_creator.extract_text import (
    apply_extraction_fields,
    clear_extraction_fields,
    get_extracted_text,
)
from retro_98_ai_creator.storage import ArchiveStore


def _api_with_tmp_store(tmp_path, monkeypatch) -> Api:
    api = Api()
    api.config = {
        "backend": {"provider": "gemini"},
        "gemini": {"text_model": "gemini-2.5-flash", "api_key": "test-key"},
        "paths": {"archives": str(tmp_path / "archives.json"), "media": "media"},
    }
    api.store = ArchiveStore(path=tmp_path / "archives.json")
    monkeypatch.setattr("retro_98_ai_creator.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "retro_98_ai_creator.media_store.load_config",
        lambda: api.config,
    )
    return api


def _wait_job(api: Api, job_id: str, timeout_s: float = 5.0) -> dict:
    steps = max(1, int(timeout_s / 0.05))
    for _ in range(steps):
        job = api.get_job(job_id)
        if job.get("status") in ("done", "error", "cancelled", "missing"):
            return job
        threading.Event().wait(0.05)
    return api.get_job(job_id)


def test_clear_and_apply_extraction_fields():
    creation = build_media_creation(
        modality="image",
        prompt="sign",
        media_path="media/a.png",
        mime_type="image/png",
        title="Sign",
        creation_id="doc_a",
    )
    updated = apply_extraction_fields(
        creation,
        text="HELLO",
        kind="ocr",
        model="gemini-2.5-flash",
        provider="gemini",
    )
    assert get_extracted_text(updated) == "HELLO"
    assert updated["meta"]["extractionKind"] == "ocr"
    assert updated["meta"]["extractionModel"] == "gemini-2.5-flash"

    cleared = clear_extraction_fields(updated)
    assert get_extracted_text(cleared) == ""
    assert "extractionKind" not in (cleared.get("meta") or {})


def test_export_creation_txt_uses_extracted_for_media(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    creation = build_media_creation(
        modality="image",
        prompt="sign",
        media_path="media/a.png",
        mime_type="image/png",
        title="Sign",
        creation_id="doc_a",
    )
    with pytest.raises(RuntimeError, match="Extract Text"):
        api.export_creation_txt(creation)

    creation = apply_extraction_fields(
        creation,
        text="HELLO WORLD",
        kind="ocr",
        model="m",
        provider="gemini",
    )
    out = api.export_creation_txt(creation)
    assert "HELLO WORLD" in out


def test_replace_creation_media_clears_extracted_text(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    (tmp_path / "media").mkdir(parents=True, exist_ok=True)
    creation = build_media_creation(
        modality="image",
        prompt="sign",
        media_path="media/doc_img1.png",
        mime_type="image/png",
        title="Shot",
        creation_id="doc_img1",
    )
    creation = apply_extraction_fields(
        creation, text="OLD", kind="ocr", model="m", provider="gemini"
    )
    api.store.upsert(creation)

    png = base64.b64encode(b"\x89PNG\r\n\x1a\nedited").decode("ascii")
    res = api.replace_creation_media(
        "doc_img1",
        f"data:image/png;base64,{png}",
        "image/png",
    )
    assert res["ok"] is True
    assert get_extracted_text(res["creation"]) == ""


def test_extract_creation_text_rejects_text_doc(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    text_doc = {
        "id": "doc_t1",
        "modality": "text",
        "title": "Note",
        "overview": "hello",
        "sections": [{"title": "Response", "content": "hello"}],
    }
    api.store.upsert(text_doc)
    res = api.extract_creation_text("doc_t1")
    assert res["ok"] is False
    assert "image or video" in (res.get("error") or "").lower()


def test_extract_creation_text_job_persists(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    (media_dir / "doc_img2.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")

    creation = build_media_creation(
        modality="image",
        prompt="sign",
        media_path="media/doc_img2.png",
        mime_type="image/png",
        title="Shot",
        creation_id="doc_img2",
    )
    api.store.upsert(creation)

    def fake_extract(creation, *, config, media_path, progress=None, cancel_event=None):
        return apply_extraction_fields(
            creation,
            text="OCR RESULT",
            kind="ocr",
            model="gemini-2.5-flash",
            provider="gemini",
        )

    monkeypatch.setattr(
        "retro_98_ai_creator.extract_text.extract_text_from_creation",
        fake_extract,
    )

    res = api.extract_creation_text("doc_img2")
    assert res["ok"] is True
    job = _wait_job(api, res["job_id"])
    assert job["status"] == "done", job
    assert get_extracted_text(job["result"]) == "OCR RESULT"
    stored = next(c for c in api.store.load() if c["id"] == "doc_img2")
    assert get_extracted_text(stored) == "OCR RESULT"


def test_extract_rejects_huggingface(tmp_path, monkeypatch):
    api = _api_with_tmp_store(tmp_path, monkeypatch)
    api.config["backend"] = {"provider": "huggingface"}
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    (media_dir / "doc_img3.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    creation = build_media_creation(
        modality="image",
        prompt="sign",
        media_path="media/doc_img3.png",
        mime_type="image/png",
        title="Shot",
        creation_id="doc_img3",
    )
    api.store.upsert(creation)

    res = api.extract_creation_text("doc_img3")
    assert res["ok"] is True
    job = _wait_job(api, res["job_id"])
    assert job["status"] == "error"
    assert "Gemini or OpenRouter" in (job.get("error") or "")
