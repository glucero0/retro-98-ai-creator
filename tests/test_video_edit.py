"""Unit tests for video_edit filtergraph and helpers (no ffmpeg required)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from retro_98_ai_creator.video_edit import (
    DEFAULT_FILTERS,
    assemble_segments,
    build_filtergraph,
    ffmpeg_available,
    has_active_filters,
    normalize_filters,
    trim_segment,
)


def test_normalize_filters_defaults():
    assert normalize_filters(None) == DEFAULT_FILTERS
    partial = normalize_filters({"brightness": 20, "grayscale": True})
    assert partial["brightness"] == 20
    assert partial["grayscale"] is True
    assert partial["saturation"] == 100


def test_has_active_filters():
    assert not has_active_filters({})
    assert has_active_filters({"brightness": 10})
    assert has_active_filters({"grayscale": True})
    assert not has_active_filters({"brightness": 0, "saturation": 100})


def test_build_filtergraph_empty():
    assert build_filtergraph({}) == ""
    assert build_filtergraph(None) == ""


def test_build_filtergraph_basic():
    vf = build_filtergraph({"brightness": 50, "contrast": -20, "saturation": 150})
    assert "eq=" in vf
    assert "brightness=" in vf
    assert "contrast=" in vf
    assert "saturation=" in vf


def test_build_filtergraph_grayscale_and_rotate():
    vf = build_filtergraph({"grayscale": True}, rotation=90)
    assert "hue=s=0" in vf
    assert "transpose=1" in vf


def test_build_filtergraph_crop_normalized():
    vf = build_filtergraph(
        {},
        crop={"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.4, "normalized": True},
        source_width=200,
        source_height=100,
    )
    assert "crop=100:40:20:20" in vf


def test_build_filtergraph_crop_absolute():
    vf = build_filtergraph(
        {},
        crop={"x": 10, "y": 20, "w": 80, "h": 60},
        source_width=200,
        source_height=100,
    )
    assert "crop=80:60:10:20" in vf


def test_build_filtergraph_sharpen_blur_vignette():
    vf = build_filtergraph({"sharpen": True, "blur": 2, "vignette": 50})
    assert "unsharp=" in vf
    assert "gblur=sigma=2.00" in vf
    assert "vignette=" in vf


def test_ffmpeg_available_shape():
    status = ffmpeg_available()
    assert "ok" in status
    if status["ok"]:
        assert status.get("ffmpeg")
    else:
        assert "error" in status


def test_apply_edits_requires_file(tmp_path):
    from retro_98_ai_creator.video_edit import apply_edits

    missing = tmp_path / "nope.mp4"
    dest = tmp_path / "out.mp4"
    with pytest.raises(FileNotFoundError):
        apply_edits(missing, dest, filters={"brightness": 10})


def test_assemble_segments_requires_file(tmp_path):
    missing = tmp_path / "nope.mp4"
    dest = tmp_path / "out.mp4"
    with pytest.raises(FileNotFoundError):
        assemble_segments(missing, dest, [{"start": 0, "end": 1}])


def test_assemble_segments_requires_ranges(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"not-a-real-video")
    dest = tmp_path / "out.mp4"
    with pytest.raises(ValueError, match="At least one segment"):
        assemble_segments(src, dest, [])
    with pytest.raises(ValueError, match="At least one segment"):
        assemble_segments(src, dest, [{"start": 0, "end": 0.01}])


def test_trim_segment_requires_file(tmp_path):
    with patch("retro_98_ai_creator.video_edit._require_ffmpeg", return_value="ffmpeg"):
        with pytest.raises(FileNotFoundError):
            trim_segment(tmp_path / "missing.mp4", tmp_path / "out.mp4", 0, 1)


def test_trim_segment_rejects_too_short(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake")
    with patch("retro_98_ai_creator.video_edit._require_ffmpeg", return_value="ffmpeg"):
        with pytest.raises(ValueError, match="too short"):
            trim_segment(src, tmp_path / "out.mp4", 1.0, 1.02)


def test_assemble_segments_single_range_uses_apply_edits(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake-mp4")
    dest = tmp_path / "out.mp4"

    def fake_apply(source, out, **kwargs):
        assert Path(source) == src
        assert kwargs.get("trim") == {"start": 0.5, "end": 2.5}
        assert kwargs.get("rotation") == 90
        Path(out).write_bytes(b"assembled")
        return Path(out)

    with patch("retro_98_ai_creator.video_edit.apply_edits", side_effect=fake_apply):
        result = assemble_segments(
            src,
            dest,
            [{"start": 0.5, "end": 2.5}],
            filters={"brightness": 10},
            rotation=90,
        )
    assert result == dest
    assert dest.read_bytes() == b"assembled"


def test_assemble_segments_drops_short_keeps_valid(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake-mp4")
    dest = tmp_path / "out.mp4"
    seen = {}

    def fake_apply(source, out, **kwargs):
        seen["trim"] = kwargs.get("trim")
        Path(out).write_bytes(b"ok")
        return Path(out)

    with patch("retro_98_ai_creator.video_edit.apply_edits", side_effect=fake_apply):
        assemble_segments(
            src,
            dest,
            [
                {"start": 0, "end": 0.02},  # dropped
                "ignore-me",
                {"start": 1.0, "end": 3.0},
            ],
        )
    assert seen["trim"] == {"start": 1.0, "end": 3.0}


def test_assemble_segments_multi_calls_trim_then_concat(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake-mp4")
    dest = tmp_path / "out.mp4"
    trim_calls: list[tuple[float, float]] = []
    counter = {"n": 0}

    def fake_temp(prefix=""):
        counter["n"] += 1
        return tmp_path / f"{prefix}{counter['n']}.mp4"

    def fake_trim(source, part, start, end):
        trim_calls.append((start, end))
        Path(part).write_bytes(b"seg")
        return Path(part)

    def fake_concat(paths, mid):
        assert len(paths) == 2
        Path(mid).write_bytes(b"mid")
        return Path(mid)

    def fake_apply(source, out, **kwargs):
        Path(out).write_bytes(b"final")
        return Path(out)

    with (
        patch("retro_98_ai_creator.video_edit.trim_segment", side_effect=fake_trim),
        patch("retro_98_ai_creator.video_edit.concat_videos", side_effect=fake_concat),
        patch("retro_98_ai_creator.video_edit.apply_edits", side_effect=fake_apply),
        patch("retro_98_ai_creator.video_edit.temp_mp4_path", side_effect=fake_temp),
    ):
        result = assemble_segments(
            src,
            dest,
            [{"start": 0, "end": 1}, {"start": 2, "end": 4}],
            filters={"grayscale": True},
        )
    assert result == dest
    assert trim_calls == [(0.0, 1.0), (2.0, 4.0)]
    assert dest.read_bytes() == b"final"
