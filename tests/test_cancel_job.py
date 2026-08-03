"""Tests for cooperative generation cancellation."""

from __future__ import annotations

import threading

import pytest

from retro_98_ai_creator.cancellation import GenerationCancelled, raise_if_cancelled


def test_raise_if_cancelled_noop():
    raise_if_cancelled(None)
    raise_if_cancelled(lambda: False)


def test_raise_if_cancelled_raises():
    with pytest.raises(GenerationCancelled):
        raise_if_cancelled(lambda: True)


def test_cancel_job_marks_cancelling():
    from retro_98_ai_creator.api import Api

    api = Api()
    evt = threading.Event()
    job_id = "gen_testcancel"
    with api._jobs_lock:
        api._cancel_events[job_id] = evt
    api._set_job(job_id, status="running", kind="generate")

    res = api.cancel_job(job_id)
    assert res["ok"] is True
    assert evt.is_set()
    job = api.get_job(job_id)
    assert job["status"] == "cancelling"


def test_cancel_job_unknown():
    from retro_98_ai_creator.api import Api

    api = Api()
    res = api.cancel_job("missing")
    assert res["ok"] is False
