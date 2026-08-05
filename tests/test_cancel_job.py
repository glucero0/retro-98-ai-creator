"""Tests for cooperative generation cancellation."""

from __future__ import annotations

import threading
import time

import pytest

from retro_98_ai_creator.cancellation import (
    GenerationCancelled,
    raise_if_cancelled,
    run_cancellable,
)


def test_raise_if_cancelled_noop():
    raise_if_cancelled(None)
    raise_if_cancelled(lambda: False)


def test_raise_if_cancelled_raises():
    with pytest.raises(GenerationCancelled):
        raise_if_cancelled(lambda: True)


def test_run_cancellable_returns_value():
    assert run_cancellable(lambda: 42) == 42


def test_run_cancellable_propagates_error():
    def boom() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        run_cancellable(boom)


def test_run_cancellable_aborts_without_waiting_for_fn():
    """Cancel must raise quickly even while the worker is still blocked."""
    started = threading.Event()
    evt = threading.Event()

    def slow() -> str:
        started.set()
        time.sleep(5)
        return "done"

    def cancel_soon() -> None:
        started.wait(timeout=2)
        time.sleep(0.05)
        evt.set()

    threading.Thread(target=cancel_soon, daemon=True).start()
    t0 = time.perf_counter()
    with pytest.raises(GenerationCancelled):
        run_cancellable(slow, evt, poll_seconds=0.05)
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.5, f"cancel waited too long: {elapsed:.2f}s"


def test_run_cancellable_raises_if_already_cancelled():
    evt = threading.Event()
    evt.set()
    with pytest.raises(GenerationCancelled):
        run_cancellable(lambda: "x", evt)


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
