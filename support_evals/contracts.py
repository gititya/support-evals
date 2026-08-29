"""Product-neutral contracts for complete customer-support evaluations.

The contracts deliberately use plain dataclasses.  Adapters and evaluation packs
can be implemented without pulling a web framework or an observability service
into the core package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Protocol, Sequence


SCHEMA_VERSION = "1.0"


class ResultStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    ABSTENTION = "abstention"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class Scenario:
    """A versioned customer situation and its success contract.

    ``context`` is the state available to the adapter.  ``expected`` is a
    product-neutral description of the outcome that evaluators may inspect;
    neither field is interpreted by the core runner.
    """

    id: str
    title: str
    opening: str
    context: Mapping[str, Any] = field(default_factory=dict)
    expected: Mapping[str, Any] = field(default_factory=dict)
    category: str = "general-support"
    tags: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("scenario id must not be empty")
        if not self.title.strip():
            raise ValueError("scenario title must not be empty")
        if not self.opening.strip():
            raise ValueError("scenario opening must not be empty")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported scenario schema: {self.schema_version}")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Scenario":
        tags = value.get("tags", ())
        return cls(
            id=str(value["id"]),
            title=str(value["title"]),
            opening=str(value["opening"]),
            context=dict(value.get("context", {})),
            expected=dict(value.get("expected", {})),
            category=str(value.get("category", "general-support")),
            tags=tuple(str(item) for item in tags),
            schema_version=str(value.get("schema_version", SCHEMA_VERSION)),
            metadata=dict(value.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "title": self.title,
            "opening": self.opening,
            "context": dict(self.context),
            "expected": dict(self.expected),
            "category": self.category,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class Event:
    """One observable event in a support journey."""

    sequence: int
    actor: str
    kind: str
    content: str = ""
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "actor": self.actor,
            "kind": self.kind,
            "content": self.content,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class Trace:
    """The conversation and observable actions produced by an adapter."""

    events: tuple[Event, ...] = ()
    final_state: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [event.to_dict() for event in self.events],
            "final_state": dict(self.final_state),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CheckResult:
    """The exact result of one deterministic or model-assisted check."""

    check_id: str
    status: ResultStatus
    summary: str
    customer_effect: str
    evidence: tuple[str, ...] = ()
    expected: Any = None
    observed: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("check id must not be empty")
        if self.status is ResultStatus.ERROR and not (self.error or self.summary):
            raise ValueError("an error check needs an error or summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status.value,
            "summary": self.summary,
            "customer_effect": self.customer_effect,
            "evidence": list(self.evidence),
            "expected": self.expected,
            "observed": self.observed,
            "error": self.error,
        }


@dataclass(frozen=True)
class EvaluatorResult:
    evaluator_id: str
    checks: tuple[CheckResult, ...]
    summary: str = ""

    @property
    def status(self) -> ResultStatus:
        return _worst_status(check.status for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_id": self.evaluator_id,
            "status": self.status.value,
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True)
class JourneyResult:
    scenario: Scenario
    completed: bool
    trace: Trace | None
    evaluators: tuple[EvaluatorResult, ...] = ()
    error: str | None = None

    @property
    def statuses(self) -> frozenset[ResultStatus]:
        """Return every outcome present in the journey, not only its headline."""

        values = {
            check.status
            for evaluator in self.evaluators
            for check in evaluator.checks
        }
        if self.error or any(not evaluator.checks for evaluator in self.evaluators):
            values.add(ResultStatus.ERROR)
        if not values:
            values.add(ResultStatus.ERROR)
        return frozenset(values)

    @property
    def status(self) -> ResultStatus:
        return _worst_status(self.statuses)

    def to_dict(self, *, include_trace: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "scenario": self.scenario.to_dict(),
            "completed": self.completed,
            "status": self.status.value,
            "error": self.error,
            "evaluators": [result.to_dict() for result in self.evaluators],
        }
        if include_trace:
            value["trace"] = self.trace.to_dict() if self.trace else None
        return value


@dataclass(frozen=True)
class RunCounts:
    requested: int
    completed: int
    passed: int
    failed: int
    error: int
    abstention: int
    unsafe: int

    def to_dict(self) -> dict[str, int]:
        return {
            "requested": self.requested,
            "completed": self.completed,
            "passed": self.passed,
            "failed": self.failed,
            "error": self.error,
            "abstention": self.abstention,
            "unsafe": self.unsafe,
        }


@dataclass(frozen=True)
class RunResult:
    profile: str
    journeys: tuple[JourneyResult, ...]
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def counts(self) -> RunCounts:
        status_sets = [journey.statuses for journey in self.journeys]
        return RunCounts(
            requested=len(self.journeys),
            completed=sum(journey.completed for journey in self.journeys),
            passed=sum(statuses == {ResultStatus.PASS} for statuses in status_sets),
            failed=sum(ResultStatus.FAIL in statuses for statuses in status_sets),
            error=sum(ResultStatus.ERROR in statuses for statuses in status_sets),
            abstention=sum(ResultStatus.ABSTENTION in statuses for statuses in status_sets),
            unsafe=sum(ResultStatus.UNSAFE in statuses for statuses in status_sets),
        )

    def to_dict(self, *, include_trace: bool = True) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "counts": self.counts.to_dict(),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "journeys": [journey.to_dict(include_trace=include_trace) for journey in self.journeys],
        }


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class ReleaseGate:
    """Fixed release rules expressed in support-lead terms."""

    min_pass_rate: float = 1.0
    max_failed: int = 0
    max_errors: int = 0
    max_abstentions: int = 0
    max_unsafe: int = 0
    require_all_completed: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.min_pass_rate <= 1:
            raise ValueError("min_pass_rate must be between 0 and 1")
        for name in ("max_failed", "max_errors", "max_abstentions", "max_unsafe"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")

    def evaluate(self, run: RunResult) -> GateResult:
        counts = run.counts
        reasons: list[str] = []
        if self.require_all_completed and counts.completed != counts.requested:
            reasons.append(f"{counts.requested - counts.completed} requested journey(s) did not complete")
        pass_rate = counts.passed / counts.requested if counts.requested else 0.0
        if pass_rate < self.min_pass_rate:
            reasons.append(f"pass rate {pass_rate:.1%} is below {self.min_pass_rate:.1%}")
        if counts.failed > self.max_failed:
            reasons.append(f"{counts.failed} failed journey(s) exceeds limit {self.max_failed}")
        if counts.error > self.max_errors:
            reasons.append(f"{counts.error} execution/evaluation error(s) exceeds limit {self.max_errors}")
        if counts.abstention > self.max_abstentions:
            reasons.append(f"{counts.abstention} abstention(s) exceeds limit {self.max_abstentions}")
        if counts.unsafe > self.max_unsafe:
            reasons.append(f"{counts.unsafe} unsafe journey(s) exceeds limit {self.max_unsafe}")
        return GateResult(passed=not reasons, reasons=tuple(reasons))


@dataclass(frozen=True)
class Profile:
    name: str
    evaluator_ids: tuple[str, ...]
    release_gate: ReleaseGate = field(default_factory=ReleaseGate)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("profile name must not be empty")
        if not self.evaluator_ids:
            raise ValueError("profile must select at least one evaluator")


class Adapter(Protocol):
    """The only product-specific surface required by the runner."""

    name: str

    def list_scenarios(self, suite: str = "default") -> Sequence[Scenario]:
        ...

    def run(self, scenario: Scenario) -> Trace:
        ...


class Evaluator(Protocol):
    evaluator_id: str

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        ...


_STATUS_PRIORITY = {
    ResultStatus.PASS: 0,
    ResultStatus.ABSTENTION: 1,
    ResultStatus.FAIL: 2,
    ResultStatus.ERROR: 3,
    ResultStatus.UNSAFE: 4,
}


def _worst_status(statuses: Sequence[ResultStatus] | Any) -> ResultStatus:
    values = list(statuses)
    if not values:
        return ResultStatus.ERROR
    return max(values, key=lambda status: _STATUS_PRIORITY[status])
