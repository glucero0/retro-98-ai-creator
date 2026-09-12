"""Lyria music generation helpers and Gemini audio routing."""

from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest

from synthetic_text_extruder.creation_utils import build_media_creation
from synthetic_text_extruder.gemini_audio import (
    extract_lyria_output,
    generate_audio_with_gemini,
    is_lyria_modality_schema_error,
    is_lyria_policy_block,
    lyria_model_candidates,
    lyria_user_error,
)

_AUDIO_SCHEMA_ERROR = (
    "Error code: 400 - {'error': {'message': \"The value 'AUDIO' is not "
    "supported for 'response_modalities[0]'. Supported values: 'text', "
    "'image', 'audio', 'video', 'document'.\", 'code': 'invalid_request'}}"
)
from synthetic_text_extruder.gemini_provider import generate_with_gemini


def test_lyria_model_candidates_retries_full_song_sibling():
    assert lyria_model_candidates("lyria-3-pro-preview") == [
        "lyria-3-pro-preview",
        "lyria-3.5",
    ]
    assert lyria_model_candidates("lyria-3.5") == [
        "lyria-3.5",
        "lyria-3-pro-preview",
    ]
    assert lyria_model_candidates("lyria-3-clip-preview") == ["lyria-3-clip-preview"]


def test_lyria_policy_error_is_readable():
    err = (
        "Error code: 400 - {'error': {'message': 'Request blocked for an "
        "unspecified policy reason. Please modify your input and retry.', "
        "'code': 'content_blocked'}}"
    )
    assert is_lyria_policy_block(err)
    msg = lyria_user_error(err, model_name="lyria-3-pro-preview")
    assert "safety" in msg.lower()
    assert "lyria-3-pro-preview" in msg
    assert "Clip" in msg


def test_lyria_modality_schema_error_is_not_policy():
    assert is_lyria_modality_schema_error(_AUDIO_SCHEMA_ERROR)
    assert not is_lyria_policy_block(_AUDIO_SCHEMA_ERROR)
    msg = lyria_user_error(_AUDIO_SCHEMA_ERROR, model_name="lyria-3-clip-preview")
    assert "request format" in msg.lower()
    assert "lyria-3-clip-preview" in msg
    assert "Gemini music generation error" not in msg


def test_extract_lyria_output_from_convenience_properties():
    payload = base64.b64encode(b"ID3fake-mp3").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="[Verse]\nNeon rain on chrome",
        steps=[],
    )
    audio, mime, lyrics = extract_lyria_output(interaction)
    assert audio == b"ID3fake-mp3"
    assert mime == "audio/mpeg"
    assert "Neon rain" in lyrics


def test_extract_lyria_output_from_steps():
    payload = base64.b64encode(b"RIFF-wav").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=None,
        output_text=None,
        steps=[
            SimpleNamespace(
                type="model_output",
                content=[
                    SimpleNamespace(type="text", text="[Chorus]\nHold on"),
                    SimpleNamespace(
                        type="audio",
                        data=payload,
                        mime_type="audio/wav",
                    ),
                ],
            )
        ],
    )
    audio, mime, lyrics = extract_lyria_output(interaction)
    assert audio == b"RIFF-wav"
    assert mime == "audio/wav"
    assert "Hold on" in lyrics


def test_build_media_creation_audio_stores_lyrics():
    creation = build_media_creation(
        modality="audio",
        prompt="A lofi beat",
        media_path="media/doc_song.mp3",
        mime_type="audio/mpeg",
        creation_id="doc_song",
        lyrics="[Verse]\nHello",
    )
    assert creation["modality"] == "audio"
    assert creation["creationType"] == "Audio"
    assert creation["sections"][0]["content"] == "[Verse]\nHello"


def test_generate_audio_with_gemini_writes_mp3(tmp_path, monkeypatch):
    payload = base64.b64encode(b"ID3generated").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="[Intro]\nSoft keys",
        steps=[],
    )
    created = {}

    class _Interactions:
        def create(self, **kwargs):
            created.update(kwargs)
            return interaction

    class _Client:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.interactions = _Interactions()

    fake_genai = SimpleNamespace(Client=_Client)
    import sys

    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    result = generate_audio_with_gemini(
        "A bright chiptune melody, instrumental only",
        gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-clip-preview"},
    )
    assert created["model"] == "lyria-3-clip-preview"
    assert created["input"] == "A bright chiptune melody, instrumental only"
    assert created["response_modalities"] == ["audio", "text"]
    assert all(item == item.lower() for item in created["response_modalities"])
    assert "AUDIO" not in created["response_modalities"]
    assert result["modality"] == "audio"
    assert result["mimeType"] == "audio/mpeg"
    media_file = tmp_path / result["mediaPath"]
    assert media_file.is_file()
    assert media_file.read_bytes() == b"ID3generated"
    assert "Soft keys" in result["sections"][0]["content"]


def test_generate_audio_with_image_basis(tmp_path, monkeypatch):
    payload = base64.b64encode(b"ID3fromimg").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="",
        steps=[],
    )
    created = {}

    class _Interactions:
        def create(self, **kwargs):
            created.update(kwargs)
            return interaction

    fake_genai = SimpleNamespace(Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions()))
    import sys

    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    result = generate_audio_with_gemini(
        "An atmospheric ambient track inspired by this image",
        gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3.5"},
        basis_media={"bytes": b"\x89PNG", "mime_type": "image/png"},
    )
    assert result["modality"] == "audio"
    assert isinstance(created["input"], list)
    assert created["input"][0]["type"] == "text"
    assert created["input"][1]["type"] == "image"
    assert result["_model"]["basis"] is True


def test_generate_audio_retries_pro_on_policy_block(tmp_path, monkeypatch):
    payload = base64.b64encode(b"ID3retry").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="",
        steps=[],
    )
    attempts: list[str] = []

    class _Interactions:
        def create(self, **kwargs):
            model = kwargs["model"]
            attempts.append(model)
            if model == "lyria-3-pro-preview":
                raise RuntimeError(
                    "Error code: 400 - {'error': {'code': 'content_blocked', "
                    "'message': 'Request blocked for an unspecified policy reason.'}}"
                )
            return interaction

    import sys

    fake_genai = SimpleNamespace(
        Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions())
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    result = generate_audio_with_gemini(
        "A bright chiptune melody, instrumental only",
        gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-pro-preview"},
    )
    assert attempts == ["lyria-3-pro-preview", "lyria-3.5"]
    assert result["_model"]["repo_id"] == "lyria-3.5"


def test_generate_audio_policy_block_on_all_candidates(tmp_path, monkeypatch):
    class _Interactions:
        def create(self, **kwargs):
            raise RuntimeError(
                "Error code: 400 - {'error': {'code': 'content_blocked', "
                "'message': 'Request blocked for an unspecified policy reason.'}}"
            )

    import sys

    fake_genai = SimpleNamespace(
        Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions())
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    with pytest.raises(RuntimeError, match="safety filters"):
        generate_audio_with_gemini(
            "sing exactly like a famous pop star",
            gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-pro-preview"},
        )


def test_generate_audio_retries_without_modalities_on_schema_error(
    tmp_path, monkeypatch
):
    payload = base64.b64encode(b"ID3schema").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="[Verse]\nFallback",
        steps=[],
    )
    calls: list[dict] = []

    class _Interactions:
        def create(self, **kwargs):
            calls.append(dict(kwargs))
            if "response_modalities" in kwargs:
                raise RuntimeError(_AUDIO_SCHEMA_ERROR)
            return interaction

    import sys

    fake_genai = SimpleNamespace(
        Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions())
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    result = generate_audio_with_gemini(
        "A bright chiptune melody, instrumental only",
        gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-clip-preview"},
    )
    assert calls
    first = calls[0]
    assert first["response_modalities"] == ["audio", "text"]
    assert "AUDIO" not in first["response_modalities"]
    last = calls[-1]
    assert "response_modalities" not in last
    assert result["modality"] == "audio"
    media_file = tmp_path / result["mediaPath"]
    assert media_file.is_file()
    assert media_file.read_bytes() == b"ID3schema"


def test_generate_audio_drops_unknown_create_kwargs(tmp_path, monkeypatch):
    payload = base64.b64encode(b"ID3notype").decode("ascii")
    interaction = SimpleNamespace(
        output_audio=SimpleNamespace(data=payload, mime_type="audio/mpeg"),
        output_text="",
        steps=[],
    )
    created = {}

    class _Interactions:
        def create(self, **kwargs):
            if "timeout" in kwargs:
                raise TypeError("create() got an unexpected keyword argument 'timeout'")
            if "response_modalities" in kwargs:
                raise TypeError(
                    "create() got an unexpected keyword argument 'response_modalities'"
                )
            created.update(kwargs)
            return interaction

    import sys

    fake_genai = SimpleNamespace(
        Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions())
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    result = generate_audio_with_gemini(
        "A bright chiptune melody, instrumental only",
        gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-clip-preview"},
    )
    assert "response_modalities" not in created
    assert "timeout" not in created
    assert result["modality"] == "audio"


def test_generate_audio_schema_error_does_not_retry_sibling(tmp_path, monkeypatch):
    attempts: list[str] = []

    class _Interactions:
        def create(self, **kwargs):
            attempts.append(kwargs["model"])
            raise RuntimeError(_AUDIO_SCHEMA_ERROR)

    import sys

    fake_genai = SimpleNamespace(
        Client=lambda api_key=None: SimpleNamespace(interactions=_Interactions())
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setattr("synthetic_text_extruder.media_store.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "synthetic_text_extruder.media_store.load_config",
        lambda: {"paths": {"media": "media"}},
    )

    with pytest.raises(RuntimeError, match="request format"):
        generate_audio_with_gemini(
            "A bright chiptune melody, instrumental only",
            gemini_cfg={"api_key": "test-key", "audio_model": "lyria-3-pro-preview"},
        )
    assert attempts
    assert all(model == "lyria-3-pro-preview" for model in attempts)
    assert "lyria-3.5" not in attempts


def test_generate_with_gemini_routes_audio(monkeypatch):
    called = {}

    def fake_audio(prompt, **kwargs):
        called["prompt"] = prompt
        return {"modality": "audio", "prompt": prompt}

    monkeypatch.setattr(
        "synthetic_text_extruder.gemini_audio.generate_audio_with_gemini",
        fake_audio,
    )
    out = generate_with_gemini(
        "Prompt",
        "General",
        "Custom",
        gemini_cfg={"api_key": "k", "audio_model": "lyria-3-clip-preview"},
        creation_description="Compose a song about starlight",
        forced_modality="audio",
    )
    assert out["modality"] == "audio"
    assert called["prompt"] == "Compose a song about starlight"


def test_generate_with_gemini_layout_basis_routes_text(monkeypatch):
    captured = {}

    def fake_text(*args, **kwargs):
        captured["basis"] = kwargs.get("basis_media")
        return {"modality": "text", "prompt": kwargs.get("prompt_text")}

    monkeypatch.setattr(
        "synthetic_text_extruder.gemini_provider._generate_text_with_gemini",
        fake_text,
    )
    out = generate_with_gemini(
        "Prompt",
        "General",
        "Custom",
        gemini_cfg={"api_key": "k", "text_model": "gemini-2.5-flash"},
        creation_description="rebuild this window",
        basis_media={
            "modality": "image",
            "bytes": b"\x89PNG",
            "mime_type": "image/png",
            "extracted_layout": {"isUi": True, "elements": []},
        },
    )
    assert out["modality"] == "text"
    assert captured["basis"]["extracted_layout"]["isUi"] is True
