"""Intent, customer risk, routing and human-handoff checks."""

from __future__ import annotations

from collections.abc import Mapping

from ..contracts import EvaluatorResult, Scenario, Trace
from ._common import agent_events, check, expected_map, result


class RoutingRiskHandoffEvaluator:
    evaluator_id = "routing-risk-handoff"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        expected = expected_map(scenario, "routing")
        agents = agent_events(trace)
        route_event = next((event for event in reversed(agents) if event.data.get("route")), None)
        observed_route = route_event.data.get("route") if route_event else None
        observed_intent = route_event.data.get("intent") if route_event else None
        observed_risk = route_event.data.get("risk") if route_event else None
        checks = []
        for name, observed, wanted, effect in (
            ("intent", observed_intent, expected.get("intent"), "The customer is understood and sent through the right support path."),
            ("route", observed_route, expected.get("route"), "The customer reaches a team that can solve the issue."),
            ("risk", observed_risk, expected.get("risk"), "The customer receives the level of care and escalation their situation needs."),
        ):
            if wanted is None:
                continue
            passed = observed == wanted
            checks.append(check(
                f"routing.{name}", passed,
                f"{name.title()} {'matches' if passed else 'does not match'} the case requirement ({wanted}).",
                effect if passed else f"The customer may be routed incorrectly or receive less care than their {name} level requires.",
                evidence=[f"routing event: {route_event.to_dict() if route_event else None}"],
                expected=wanted, observed=observed,
            ))

        if expected.get("handoff_required") is not None:
            handoff = next((event.data.get("handoff") for event in reversed(trace.events) if event.data.get("handoff")), None)
            required_fields = [str(item) for item in expected.get("handoff_fields", ("summary", "customer_goal", "attempts", "next_action"))]
            missing = [field for field in required_fields if not isinstance(handoff, Mapping) or not handoff.get(field)]
            provided = handoff is not None
            passed = (bool(expected["handoff_required"]) == provided) and (not expected["handoff_required"] or not missing)
            checks.append(check(
                "routing.handoff-complete", passed,
                f"Human handoff {'is complete' if passed else 'is missing or incomplete'}.",
                "The next support person receives the customer’s problem, work already done and the next step."
                if passed else "The customer may have to repeat the problem or wait while the next team reconstructs the case.",
                evidence=[f"handoff: {handoff!r}"], expected={"required": expected["handoff_required"], "fields": required_fields},
                observed=handoff,
            ))
        if not checks:
            checks.append(check(
                "routing.trace-present", bool(agents),
                "Routing evidence is present." if agents else "No agent routing evidence is present.",
                "The customer’s route can be reviewed." if agents else "The customer’s route cannot be reviewed.",
                evidence=[f"agent event count: {len(agents)}"], observed=len(agents),
            ))
        return result(self.evaluator_id, checks, "Intent, risk, route and handoff checks.")


IntentRiskRoutingEvaluator = RoutingRiskHandoffEvaluator
