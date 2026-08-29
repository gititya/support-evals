"""Execution and adapter registration for Support Evals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable, Mapping

from .contracts import (
    Adapter,
    Event,
    Evaluator,
    JourneyResult,
    Profile,
    RunResult,
    Scenario,
    Trace,
)


class AdapterRegistry:
    def __init__(self, adapters: Iterable[Adapter] = ()) -> None:
        self._adapters: dict[str, Adapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: Adapter) -> None:
        if not adapter.name.strip():
            raise ValueError("adapter name must not be empty")
        if adapter.name in self._adapters:
            raise ValueError(f"adapter already registered: {adapter.name}")
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> Adapter:
        try:
            return self._adapters[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._adapters)) or "none"
            raise KeyError(f"unknown adapter {name!r}; available: {available}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))


def run_suite(
    adapter: Adapter,
    scenarios: Iterable[Scenario],
    *,
    profile: Profile,
    evaluators: Mapping[str, Evaluator] | Iterable[Evaluator] = (),
) -> RunResult:
    """Run every requested scenario, retaining a result for every request.

    Adapter and evaluator exceptions become explicit error journeys.  A single
    broken case never removes that case from the requested denominator.
    """

    evaluator_map = (
        dict(evaluators)
        if isinstance(evaluators, Mapping)
        else {evaluator.evaluator_id: evaluator for evaluator in evaluators}
    )
    missing = tuple(evaluator_id for evaluator_id in profile.evaluator_ids if evaluator_id not in evaluator_map)
    selected = [evaluator_map[evaluator_id] for evaluator_id in profile.evaluator_ids if evaluator_id in evaluator_map]
    started = _now()
    journeys: list[JourneyResult] = []
    for scenario in scenarios:
        try:
            trace = adapter.run(scenario)
        except Exception as exc:  # adapter boundary: preserve the case as an error
            journeys.append(JourneyResult(scenario=scenario, completed=False, trace=None, error=str(exc)))
            continue
        if missing:
            journeys.append(
                JourneyResult(
                    scenario=scenario,
                    completed=True,
                    trace=trace,
                    error=f"missing evaluator(s): {', '.join(missing)}",
                )
            )
            continue
        results = []
        evaluation_error: str | None = None
        for evaluator in selected:
            try:
                results.append(evaluator.evaluate(scenario, trace))
            except Exception as exc:  # evaluator boundary: preserve completed trace
                evaluation_error = str(exc)
                break
        journeys.append(
            JourneyResult(
                scenario=scenario,
                completed=True,
                trace=trace,
                evaluators=tuple(results),
                error=evaluation_error,
            )
        )
    return RunResult(profile=profile.name, journeys=tuple(journeys), started_at=started, finished_at=_now())


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class FixtureAdapter:
    """Deterministic adapter for demos and tests; no model or network is used."""

    scenarios: tuple[Scenario, ...] = ()
    name: str = "fixture"

    def list_scenarios(self, suite: str = "default") -> tuple[Scenario, ...]:
        return self.scenarios or default_fixture_scenarios()

    def run(self, scenario: Scenario) -> Trace:
        outcome = str(scenario.metadata.get("fixture_outcome", "pass"))
        return Trace(
            events=(
                # The fixture is intentionally boring: it gives packs stable
                # evidence while leaving support-specific scoring to evaluators.
                Event(
                    sequence=1, actor="customer", kind="message", content=scenario.opening
                ),
                Event(
                    sequence=2, actor="agent", kind="message", content="Fixture response"
                ),
            ),
            final_state={"fixture_outcome": outcome},
            metadata={"adapter": self.name, "fixture_outcome": outcome},
        )


def default_fixture_scenarios() -> tuple[Scenario, ...]:
    return (
        Scenario(
            id="fixture-tech-login",
            title="Customer cannot sign in",
            opening="I cannot sign in to my account.",
            category="technical-support",
            expected={"resolution": "account access restored or safe handoff"},
        ),
        Scenario(
            id="fixture-product-how-to",
            title="Customer asks how to use a feature",
            opening="How do I turn on notifications?",
            category="product-support",
            expected={"resolution": "clear instructions or safe handoff"},
        ),
    )
