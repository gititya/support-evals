"""Exact answer and policy checks for support conversations.

These checks use facts and claims recorded by the adapter.  They do not ask a
language model whether a reply *sounds* good, so their verdict is repeatable.
"""

from __future__ import annotations

from typing import Any

from ..contracts import EvaluatorResult, Scenario, Trace
from ._common import agent_events, check, expected_map, result, values


class AnswerPolicyEvaluator:
    evaluator_id = "answer-policy"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        expected = expected_map(scenario, "answer_policy")
        agents = agent_events(trace)
        observed_facts = set().union(*(values(event, "facts") for event in agents))
        observed_basis = set().union(*(values(event, "policy_basis") for event in agents))
        observed_claims = set().union(*(values(event, "claims") for event in agents))
        checks = []

        required = [str(item) for item in expected.get("required_facts", ())]
        for fact in required:
            checks.append(
                check(
                    f"answer.required.{fact}",
                    fact in observed_facts,
                    f"Required support fact {'was' if fact in observed_facts else 'was not'} recorded in the agent answer: {fact}.",
                    "The customer receives the key information needed to understand or act on the answer."
                    if fact in observed_facts
                    else "The customer may leave without the information needed to solve the issue or choose the next step.",
                    evidence=[f"agent facts: {sorted(observed_facts)}"],
                    expected=fact,
                    observed=sorted(observed_facts),
                )
            )

        required_policy = [str(item) for item in expected.get("required_policy_basis", ())]
        for policy_id in required_policy:
            checks.append(
                check(
                    f"answer.policy.{policy_id}",
                    policy_id in observed_basis,
                    f"Policy basis {'is' if policy_id in observed_basis else 'is not'} present: {policy_id}.",
                    "The customer gets an answer tied to the support policy for their case."
                    if policy_id in observed_basis
                    else "The customer may receive an answer that conflicts with the company policy.",
                    evidence=[f"policy basis: {sorted(observed_basis)}"],
                    expected=policy_id,
                    observed=sorted(observed_basis),
                )
            )

        forbidden = [str(item) for item in expected.get("forbidden_claims", ())]
        for claim in forbidden:
            present = claim in observed_claims
            checks.append(
                check(
                    f"answer.no-unsupported.{claim}",
                    not present,
                    f"Unsupported claim {'was not made' if not present else 'was made'}: {claim}.",
                    "The customer is protected from a promise or diagnosis the support record does not support."
                    if not present
                    else "The customer may rely on a promise or diagnosis that the support record cannot support.",
                    evidence=[f"agent claims: {sorted(observed_claims)}"],
                    expected=f"claim absent: {claim}",
                    observed=claim if present else None,
                )
            )

        if not checks:
            checks.append(
                check(
                    "answer.trace-present",
                    bool(agents),
                    "An agent answer event is present." if agents else "No agent answer event is present.",
                    "The customer receives a response from support."
                    if agents
                    else "The customer receives no support response.",
                    evidence=[f"agent event count: {len(agents)}"],
                    observed=len(agents),
                )
            )
        return result(self.evaluator_id, checks, "Exact facts, policy basis and forbidden-claim checks.")


# A descriptive alias helps callers choose the pack by the support task name.
AnswerQualityEvaluator = AnswerPolicyEvaluator


def answer_policy_evaluator() -> AnswerPolicyEvaluator:
    return AnswerPolicyEvaluator()
