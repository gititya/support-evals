"""Intent, customer risk, routing and human-handoff checks."""

from __future__ import annotations

from collections.abc import Mapping

from ..contracts import EvaluatorResult, Scenario, Trace
from ._common import agent_events, check, expected_map, result


_HOST_RELEASE_ACTORS = frozenset({"system", "tool"})
_HOST_RELEASE_KINDS = frozenset({"handoff_release"})
_OVERRIDE_FIELDS = ("released_by", "reason", "recipient")
_PLACEHOLDER_VALUES = frozenset({"", "-", "?", "na", "n/a", "none", "placeholder", "tbd", "todo", "unknown", "unspecified"})


def _is_host_release(event) -> bool:
    return event.actor in _HOST_RELEASE_ACTORS and event.kind in _HOST_RELEASE_KINDS


def _override_missing(value: object) -> list[str]:
    if not isinstance(value, Mapping):
        return list(_OVERRIDE_FIELDS)
    missing = []
    for field in _OVERRIDE_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip() or item.strip().lower() in _PLACEHOLDER_VALUES:
            missing.append(field)
    if any(isinstance(value.get(key), str) and value[key].strip().lower() == "vip_customer"
           for key in ("reason", "reason_code")):
        missing.append("non_vip_urgency_reason")
    return missing


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

        override_occurrences = [
            event for event in trace.events
            if "urgent_override" in event.data
        ]
        for index, event in enumerate(override_occurrences, start=1):
            override = event.data.get("urgent_override")
            missing = _override_missing(override)
            host_release = _is_host_release(event)
            passed = host_release and not missing
            if not host_release:
                summary = "Urgent handoff override is asserted by a non-host event."
            elif missing:
                summary = f"Urgent handoff override is incomplete (missing: {', '.join(missing)})."
            else:
                summary = "Urgent handoff override is recorded by a host release event."
            checks.append(check(
                "routing.urgent-handoff-override" if index == 1 else f"routing.urgent-handoff-override.{index}",
                passed,
                summary,
                "The urgent handoff has an accountable releaser, reason and recipient." if passed
                else "The urgent handoff release cannot be held accountable from this event.",
                evidence=[f"urgent override event: {event.to_dict()}"],
                expected={"host_actor": sorted(_HOST_RELEASE_ACTORS), "host_kind": sorted(_HOST_RELEASE_KINDS), "fields": list(_OVERRIDE_FIELDS), "vip_alone_allowed": False},
                observed={"host_release": host_release, "urgent_override": override, "missing": missing},
            ))

        if expected.get("urgent_handoff_override_required"):
            host_releases = [event for event in trace.events if _is_host_release(event)]
            if not host_releases:
                checks.append(check(
                    "routing.urgent-handoff-override-required",
                    False,
                    "Urgent handoff override is required, but no host release event is present.",
                    "The urgent handoff cannot be shown to have an accountable release decision.",
                    evidence=["host release event count: 0"],
                    expected=True,
                    observed=False,
                ))
            else:
                for index, event in enumerate(host_releases, start=1):
                    if "urgent_override" in event.data:
                        continue
                    checks.append(check(
                        "routing.urgent-handoff-override-required" if index == 1 else f"routing.urgent-handoff-override-required.{index}",
                        False,
                        "Urgent handoff override is required, but this host release has none.",
                        "The urgent handoff release cannot be held accountable from this event.",
                        evidence=[f"host release event: {event.to_dict()}"],
                        expected=True,
                        observed=False,
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
