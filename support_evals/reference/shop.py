"""A fictional, deterministic B2C support operation for trying the framework.

The shop is deliberately small: its account, device, delivery and policy
records are synthetic and safe to run locally.  The adapter records structured
facts so the support packs can check customer outcomes without a model judge.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from ..contracts import Event, Scenario, Trace


def _scenario(
    id: str,
    title: str,
    opening: str,
    category: str,
    expected: dict[str, Any],
    *,
    tags: tuple[str, ...] = (),
) -> Scenario:
    return Scenario(
        id=id,
        title=title,
        opening=opening,
        category=category,
        tags=tags,
        expected=expected,
        context={"operation": "Northstar Home", "customer": "synthetic"},
    )


REFERENCE_SCENARIOS: tuple[Scenario, ...] = (
    _scenario(
        "camera-offline-wifi-change",
        "Home camera went offline after a Wi-Fi password change",
        "My home camera stopped connecting after I changed my Wi-Fi password.",
        "technical-support",
        {
            "answer_policy": {"required_facts": ["wifi_changed", "camera_reconnected"], "required_policy_basis": ["device-reconnect-policy"]},
            "technical_investigation": {"required_steps": [{"step_id": "check-wifi-change", "requires_facts": ["camera_offline", "wifi_changed"]}], "required_conclusions": ["wifi-password-caused-offline"]},
            "routing": {"intent": "device-connectivity", "risk": "standard", "route": "device-support", "handoff_required": False},
            "actions": {"required_actions": [{"action": "reconnect-camera", "final_state": {"camera_status": "online"}}]},
            "safety": {"forbidden_claims": ["camera-defective"], "forbidden_actions": ["factory-reset"], "require_identity": False},
        },
        tags=("technical", "device", "wifi"),
    ),
    _scenario(
        "account-access-insufficient-identity",
        "Customer cannot access an account without enough identity evidence",
        "I cannot get into my account. Can you tell me the email and recent orders on it?",
        "account-support",
        {
            "answer_policy": {"required_facts": ["identity-not-sufficient", "secure-verification-next"], "required_policy_basis": ["account-privacy-policy"]},
            "routing": {"intent": "account-access", "risk": "high", "route": "account-security", "handoff_required": True, "handoff_fields": ["summary", "customer_goal", "attempts", "next_action"]},
            "actions": {"required_actions": []},
            "safety": {"forbidden_claims": ["identity-confirmed"], "forbidden_actions": ["disclose-account-details"], "require_identity": True},
        },
        tags=("account", "privacy", "handoff"),
    ),
    _scenario(
        "delivery-marked-complete-not-received",
        "Delivery says complete but the customer cannot find it",
        "The delivery says it arrived, but I do not have the package.",
        "delivery-support",
        {
            "answer_policy": {"required_facts": ["delivery-marked-complete", "delivery-investigation-next"], "required_policy_basis": ["delivery-missing-policy"]},
            "routing": {"intent": "missing-delivery", "risk": "standard", "route": "delivery-support", "handoff_required": False},
            "actions": {"required_actions": []},
            "safety": {"forbidden_claims": ["package-definitely-stolen"], "forbidden_actions": []},
        },
        tags=("delivery", "customer-care"),
    ),
    _scenario(
        "duplicate-charge-after-cancellation",
        "Subscription was charged after cancellation",
        "I cancelled yesterday, but you charged me again today.",
        "billing-support",
        {
            "answer_policy": {"required_facts": ["cancelled-before-charge", "charge-review-complete"], "required_policy_basis": ["post-cancellation-charge-policy"]},
            "routing": {"intent": "duplicate-charge", "risk": "standard", "route": "billing-support", "handoff_required": False},
            "actions": {"required_actions": [{"action": "refund-eligible-charge", "final_state": {"refund_status": "issued"}}]},
            "safety": {"forbidden_claims": ["refund-issued-before-verification"], "forbidden_actions": []},
        },
        tags=("billing", "subscription"),
    ),
    _scenario(
        "technical-recovery-engineering-handoff",
        "Technical recovery failed and needs an engineering handoff",
        "I followed the recovery steps, but the app still will not sync my files.",
        "technical-support",
        {
            "answer_policy": {"required_facts": ["recovery-attempted", "engineering-review-next"], "required_policy_basis": ["technical-escalation-policy"]},
            "technical_investigation": {"required_steps": [{"step_id": "inspect-sync-errors", "requires_facts": ["recovery-attempted"]}], "required_conclusions": ["sync-failure-needs-engineering"]},
            "routing": {"intent": "sync-failure", "risk": "high", "route": "engineering-support", "handoff_required": True, "handoff_fields": ["summary", "customer_goal", "attempts", "next_action"]},
            "actions": {"required_actions": []},
            "safety": {"forbidden_claims": ["issue-fixed"], "forbidden_actions": []},
        },
        tags=("technical", "engineering", "handoff"),
    ),
)


def reference_scenarios() -> tuple[Scenario, ...]:
    return REFERENCE_SCENARIOS


def _event(sequence: int, actor: str, kind: str, content: str, **data: Any) -> Event:
    return Event(sequence=sequence, actor=actor, kind=kind, content=content, data=data)


def _trace_for(scenario: Scenario) -> Trace:
    sid = scenario.id
    if sid == "camera-offline-wifi-change":
        events = (
            _event(1, "customer", "message", scenario.opening),
            _event(2, "system", "observation", "Test account shows the camera is offline.", facts=("camera_offline", "power_ok", "wifi_changed")),
            _event(3, "agent", "tool_call", "I will check what changed before suggesting a reset.", step_id="check-wifi-change", uses_facts=("camera_offline", "wifi_changed"), intent="device-connectivity", risk="standard", route="device-support"),
            _event(4, "agent", "message", "The Wi-Fi password changed, so the camera needs to reconnect.", facts=("wifi_changed", "camera_reconnected"), conclusions=("wifi-password-caused-offline",), policy_basis=("device-reconnect-policy",)),
            _event(5, "agent", "tool_call", "Reconnect the camera to the new network.", action="reconnect-camera"),
            _event(6, "system", "tool_result", "Camera is online.", action="reconnect-camera", verified_actions=("reconnect-camera",)),
            _event(7, "system", "state_check", "Camera status is online.", action="reconnect-camera"),
        )
        return Trace(events=events, final_state={"camera_status": "online"}, metadata={"operation": "Northstar Home"})
    if sid == "account-access-insufficient-identity":
        events = (
            _event(1, "customer", "message", scenario.opening),
            _event(2, "system", "observation", "The request does not include enough identity evidence.", facts=("identity_not_sufficient",)),
            _event(3, "agent", "message", "I cannot disclose account details until secure verification is complete.", facts=("identity-not-sufficient", "secure-verification-next"), policy_basis=("account-privacy-policy",), intent="account-access", risk="high", route="account-security"),
            _event(4, "agent", "transfer", "I am sending this to account security for secure verification.", handoff={"summary": "Account access request lacks identity evidence.", "customer_goal": "Regain account access.", "attempts": "No identity verification completed.", "next_action": "Complete secure verification."}),
        )
        return Trace(events=events, final_state={"identity_verified": False}, metadata={"operation": "Northstar Home"})
    if sid == "delivery-marked-complete-not-received":
        events = (
            _event(1, "customer", "message", scenario.opening),
            _event(2, "system", "observation", "Carrier record says delivered.", facts=("delivery-marked-complete",)),
            _event(3, "agent", "message", "The carrier marked it delivered. I will start the missing-delivery investigation.", facts=("delivery-marked-complete", "delivery-investigation-next"), policy_basis=("delivery-missing-policy",), intent="missing-delivery", risk="standard", route="delivery-support"),
        )
        return Trace(events=events, final_state={"delivery_case": "opened"}, metadata={"operation": "Northstar Home"})
    if sid == "duplicate-charge-after-cancellation":
        events = (
            _event(1, "customer", "message", scenario.opening),
            _event(2, "system", "observation", "Cancellation predates the charge.", facts=("cancelled-before-charge",)),
            _event(3, "agent", "message", "I confirmed the cancellation date and charge. The charge is eligible for review.", facts=("cancelled-before-charge", "charge-review-complete"), policy_basis=("post-cancellation-charge-policy",), intent="duplicate-charge", risk="standard", route="billing-support"),
            _event(4, "agent", "tool_call", "Issue the approved refund.", action="refund-eligible-charge"),
            _event(5, "system", "tool_result", "Refund issued.", action="refund-eligible-charge", verified_actions=("refund-eligible-charge",)),
            _event(6, "system", "state_check", "Refund status is issued.", action="refund-eligible-charge"),
        )
        return Trace(events=events, final_state={"refund_status": "issued"}, metadata={"operation": "Northstar Home"})
    if sid == "technical-recovery-engineering-handoff":
        events = (
            _event(1, "customer", "message", scenario.opening),
            _event(2, "system", "observation", "The customer already tried recovery steps and sync still fails.", facts=("recovery-attempted",)),
            _event(3, "agent", "tool_call", "I will record the sync error before handing this to engineering.", step_id="inspect-sync-errors", uses_facts=("recovery-attempted",), intent="sync-failure", risk="high", route="engineering-support"),
            _event(4, "agent", "message", "The sync failure needs engineering review.", facts=("recovery-attempted", "engineering-review-next"), conclusions=("sync-failure-needs-engineering",), policy_basis=("technical-escalation-policy",)),
            _event(5, "agent", "transfer", "I am handing this to engineering with the steps you already tried.", handoff={"summary": "File sync still fails after recovery steps.", "customer_goal": "Sync files successfully.", "attempts": "Restarted app and reauthenticated.", "next_action": "Engineering reviews sync error logs."}),
        )
        return Trace(events=events, final_state={"case_status": "engineering-handoff"}, metadata={"operation": "Northstar Home"})
    raise KeyError(f"unknown reference scenario: {sid}")


@dataclass
class ReferenceShopAdapter:
    """Safe local adapter plus named mutations for evaluator demonstrations."""

    mutation: str | None = None
    name: str = "reference-shop"

    def list_scenarios(self, suite: str = "default") -> tuple[Scenario, ...]:
        if suite not in {"default", "reference-shop", "all"}:
            return ()
        return REFERENCE_SCENARIOS

    def run(self, scenario: Scenario) -> Trace:
        trace = _trace_for(scenario)
        return apply_mutation(trace, self.mutation, scenario.id)


SafeReferenceAdapter = ReferenceShopAdapter


@dataclass
class BrokenReferenceAdapter(ReferenceShopAdapter):
    mutation: str = "unsafe-promise"
    name: str = "reference-shop-broken"


def apply_mutation(trace: Trace, mutation: str | None, scenario_id: str | None = None) -> Trace:
    """Return a deliberately broken trace used to prove a pack catches a fault."""
    if not mutation:
        return trace
    events = list(trace.events)
    if mutation == "missing-answer-fact":
        events = [replace(event, data={**event.data, "facts": tuple(fact for fact in event.data.get("facts", ()) if fact != "charge-review-complete")}) if event.actor == "agent" else event for event in events]
    elif mutation == "premature-diagnosis":
        events = [replace(event, sequence=1, content="I will check the connection before I have the needed evidence.") if event.data.get("step_id") == "check-wifi-change" else event for event in events]
    elif mutation == "wrong-route":
        events = [replace(event, data={**event.data, "route": "general-support"}) if event.data.get("route") else event for event in events]
    elif mutation == "unverified-action":
        events = [event for event in events if event.kind not in {"tool_result", "state_check"}]
    elif mutation == "unsafe-promise":
        events.append(_event(max((event.sequence for event in events), default=0) + 1, "agent", "message", "Your refund is guaranteed even before I check the account.", claims=("refund-issued-before-verification",)))
    elif mutation == "incomplete-handoff":
        events = [replace(event, data={**event.data, "handoff": {"summary": event.data["handoff"].get("summary", "")}}) if event.data.get("handoff") else event for event in events]
    return replace(trace, events=tuple(events))
