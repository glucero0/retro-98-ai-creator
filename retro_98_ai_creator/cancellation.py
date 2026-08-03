"""Cooperative cancellation for long-running generation jobs."""

from __future__ import annotations

from typing import Callable


class GenerationCancelled(Exception):
    """Raised when the user cancels an in-flight generation job."""


def raise_if_cancelled(cancel_check: Callable[[], bool] | None) -> None:
    if cancel_check and cancel_check():
        raise GenerationCancelled("Cancelled by user")
