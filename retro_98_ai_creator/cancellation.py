"""Cooperative cancellation for long-running generation jobs."""

from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class GenerationCancelled(Exception):
    """Raised when the user cancels an in-flight generation job."""


def raise_if_cancelled(cancel_check: Callable[[], bool] | None) -> None:
    if cancel_check and cancel_check():
        raise GenerationCancelled("Cancelled by user")


def run_cancellable(
    fn: Callable[[], T],
    cancel_event: Any = None,
    *,
    poll_seconds: float = 0.25,
) -> T:
    """
    Run ``fn`` on a daemon thread and stop waiting if ``cancel_event`` is set.

    Used around blocking provider HTTP calls (Gemini / OpenRouter) that cannot
    be aborted mid-request. The orphaned call may still finish in the background;
    we only stop blocking the job so Cancel does not hang the UI.
    """
    raise_if_cancelled(
        (lambda: bool(cancel_event is not None and cancel_event.is_set()))
        if cancel_event is not None
        else None
    )

    box: dict[str, Any] = {}
    err: dict[str, BaseException] = {}

    def runner() -> None:
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 — re-raised on joinerside
            err["exc"] = exc

    thread = threading.Thread(target=runner, daemon=True, name="cancellable-call")
    thread.start()
    while thread.is_alive():
        if cancel_event is not None and cancel_event.is_set():
            raise GenerationCancelled("Cancelled by user")
        thread.join(timeout=max(0.05, float(poll_seconds)))

    if "exc" in err:
        raise err["exc"]
    return box["value"]  # type: ignore[no-any-return]
