"""Small import boundary for future EVA or tau-bench trace adapters.

This module only normalizes already-captured data.  It is intentionally not a
call engine and does not open a microphone, place a call, or contact a vendor.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..contracts import Event, Trace


def capture_to_trace(capture: Mapping[str, Any]) -> Trace:
    """Convert a provider-neutral captured-trace dictionary into ``Trace``.

    A future EVA or tau-bench adapter should map its export to this shape before
    evaluation. Required event fields are ``sequence``, ``actor`` and
    ``kind``; provider-specific fields belong under ``data``.
    """

    raw_events = capture.get("events", ())
    events = tuple(
        Event(
            sequence=int(raw["sequence"]),
            actor=str(raw["actor"]),
            kind=str(raw["kind"]),
            content=str(raw.get("content", "")),
            data=dict(raw.get("data", {})),
        )
        for raw in raw_events
    )
    return Trace(events=events, final_state=dict(capture.get("final_state", {})), metadata=dict(capture.get("metadata", {})))
