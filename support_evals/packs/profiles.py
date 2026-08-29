"""Fixed evaluator sets for common support-team release reviews."""

from __future__ import annotations

from ..contracts import Profile, ReleaseGate
from .actions import ToolFinalStateEvaluator
from .answer_policy import AnswerPolicyEvaluator
from .routing import RoutingRiskHandoffEvaluator
from .safety import UnsafeAdversarialEvaluator
from .technical import TechnicalInvestigationEvaluator


def support_evaluators() -> tuple[object, ...]:
    """Return the standard deterministic packs in a stable order."""
    return (
        AnswerPolicyEvaluator(),
        TechnicalInvestigationEvaluator(),
        RoutingRiskHandoffEvaluator(),
        ToolFinalStateEvaluator(),
        UnsafeAdversarialEvaluator(),
    )


def standard_profile(name: str = "support-standard") -> Profile:
    return Profile(
        name=name,
        evaluator_ids=tuple(evaluator.evaluator_id for evaluator in support_evaluators()),
        release_gate=ReleaseGate(min_pass_rate=1.0, max_failed=0, max_errors=0, max_abstentions=0, max_unsafe=0),
    )
