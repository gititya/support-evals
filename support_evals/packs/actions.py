"""Checks that support actions happened and their final state was verified."""

from __future__ import annotations

from collections.abc import Mapping

from ..contracts import EvaluatorResult, Scenario, Trace
from ._common import check, expected_map, result, values


class ToolFinalStateEvaluator:
    evaluator_id = "tool-final-state"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        expected = expected_map(scenario, "actions")
        checks = []
        action_events = [event for event in trace.events if event.kind in {"tool_call", "action"}]
        verification_events = [event for event in trace.events if event.kind in {"tool_result", "state_check", "verification"}]
        for item in expected.get("required_actions", ()):
            if isinstance(item, str):
                item = {"action": item}
            action = str(item.get("action"))
            matching = [event for event in action_events if event.data.get("action") == action]
            performed = bool(matching)
            verified = any(
                event.sequence > matching[-1].sequence and (
                    event.data.get("action") == action or action in values(event, "verified_actions")
                )
                for event in verification_events
            ) if matching else False
            expected_state = item.get("final_state")
            state_ok = True
            if isinstance(expected_state, Mapping):
                state_ok = all(trace.final_state.get(str(key)) == value for key, value in expected_state.items())
            passed = performed and verified and state_ok
            checks.append(check(
                f"action.{action}", passed,
                f"Support action {action} {'was completed and verified' if passed else 'was not fully completed or verified'}.",
                "The customer’s requested support action is reflected in the account or case record."
                if passed else "The customer may be told an action happened when the account or case record does not show it.",
                evidence=[f"action events: {[event.to_dict() for event in matching]}", f"final state: {dict(trace.final_state)}"],
                expected={"action": action, "final_state": dict(expected_state) if isinstance(expected_state, Mapping) else expected_state},
                observed={"performed": performed, "verified": verified, "final_state": dict(trace.final_state)},
            ))
        if not checks:
            checks.append(check(
                "action.trace-present", bool(trace.events),
                "Action trace is present." if trace.events else "No action trace is present.",
                "The customer outcome can be checked." if trace.events else "The customer outcome cannot be checked.",
                evidence=[f"event count: {len(trace.events)}"], observed=len(trace.events),
            ))
        return result(self.evaluator_id, checks, "Tool-call and final account/case state verification.")


ActionVerificationEvaluator = ToolFinalStateEvaluator
