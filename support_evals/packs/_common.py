"""Small helpers shared by the deterministic support evaluation packs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..contracts import CheckResult, Event, ResultStatus, Scenario, Trace


def events(trace: Trace, *, actor: str | None = None, kind: str | None = None) -> list[Event]:
    """Return trace events matching observable actor/kind fields."""
    return [
        event
        for event in trace.events
        if (actor is None or event.actor == actor) and (kind is None or event.kind == kind)
    ]


def agent_events(trace: Trace) -> list[Event]:
    return events(trace, actor="agent")


def values(event: Event, key: str) -> set[str]:
    value = event.data.get(key, ())
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value}
    return set()


def first_agent_event(trace: Trace, *, kind: str | None = None) -> Event | None:
    matching = agent_events(trace)
    if kind is not None:
        matching = [event for event in matching if event.kind == kind]
    return matching[0] if matching else None


def check(
    check_id: str,
    passed: bool,
    summary: str,
    customer_effect: str,
    *,
    evidence: Iterable[str] = (),
    expected: Any = None,
    observed: Any = None,
    status: ResultStatus | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        status=status or (ResultStatus.PASS if passed else ResultStatus.FAIL),
        summary=summary,
        customer_effect=customer_effect,
        evidence=tuple(str(item) for item in evidence),
        expected=expected,
        observed=observed,
    )


def expected_map(scenario: Scenario, key: str) -> Mapping[str, Any]:
    value = scenario.expected.get(key, {})
    return value if isinstance(value, Mapping) else {}


def result(evaluator_id: str, checks: Iterable[CheckResult], summary: str = ""):
    from ..contracts import EvaluatorResult

    return EvaluatorResult(evaluator_id=evaluator_id, checks=tuple(checks), summary=summary)
