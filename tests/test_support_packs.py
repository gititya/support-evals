import unittest

from support_evals import Event, Profile, ReleaseGate, ResultStatus, Scenario, Trace, run_suite
from support_evals.packs import (
    AnswerPolicyEvaluator,
    RoutingRiskHandoffEvaluator,
    TechnicalInvestigationEvaluator,
    ToolFinalStateEvaluator,
    UnsafeAdversarialEvaluator,
    standard_profile,
    support_evaluators,
)
from support_evals.reference import ReferenceShopAdapter
from support_evals.voice import capture_to_trace


class SupportPackTests(unittest.TestCase):
    def setUp(self):
        self.scenario = ReferenceShopAdapter().list_scenarios()[0]

    def run_one(self, mutation, evaluator, scenario_id=None):
        adapter = ReferenceShopAdapter(mutation=mutation)
        scenario = next(item for item in adapter.list_scenarios() if item.id == (scenario_id or self.scenario.id))
        profile = Profile(name="one", evaluator_ids=(evaluator.evaluator_id,), release_gate=ReleaseGate())
        return run_suite(adapter, (scenario,), profile=profile, evaluators=(evaluator,)).journeys[0]

    def test_reference_operation_passes_all_packs(self):
        adapter = ReferenceShopAdapter()
        result = run_suite(adapter, adapter.list_scenarios(), profile=standard_profile(), evaluators=support_evaluators())
        self.assertEqual(result.counts.to_dict(), {"requested": 5, "completed": 5, "passed": 5, "failed": 0, "error": 0, "abstention": 0, "unsafe": 0})
        self.assertTrue(all(journey.trace and journey.trace.events for journey in result.journeys))
        self.assertTrue(all(check.customer_effect for journey in result.journeys for evaluation in journey.evaluators for check in evaluation.checks))

    def test_answer_pack_catches_missing_fact(self):
        journey = self.run_one("missing-answer-fact", AnswerPolicyEvaluator(), "duplicate-charge-after-cancellation")
        self.assertEqual(journey.status, ResultStatus.FAIL)

    def test_technical_pack_catches_premature_diagnosis(self):
        journey = self.run_one("premature-diagnosis", TechnicalInvestigationEvaluator())
        self.assertEqual(journey.status, ResultStatus.FAIL)

    def test_technical_pack_keeps_an_early_invalid_repeat_visible(self):
        scenario = Scenario(
            id="repeated-step",
            title="Repeated troubleshooting step",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        trace = Trace(events=(
            Event(1, "agent", "tool_call", data={"step_id": "check-wifi"}),
            Event(2, "system", "observation", data={"facts": ("wifi_changed",)}),
            Event(3, "agent", "tool_call", data={"step_id": "check-wifi"}),
        ))

        result = TechnicalInvestigationEvaluator().evaluate(scenario, trace)

        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertEqual([check.check_id for check in result.checks], ["technical.step.check-wifi", "technical.step.check-wifi.2"])
        self.assertEqual([check.status for check in result.checks], [ResultStatus.FAIL, ResultStatus.PASS])
        self.assertEqual([check.observed["step_sequence"] for check in result.checks], [1, 3])

    def test_technical_pack_accepts_a_step_after_an_observation(self):
        scenario = Scenario(
            id="supported-step",
            title="Supported troubleshooting step",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        trace = Trace(events=(
            Event(1, "system", "observation", data={"facts": ("wifi_changed",)}),
            Event(2, "agent", "tool_call", data={"step_id": "check-wifi"}),
        ))

        result = TechnicalInvestigationEvaluator().evaluate(scenario, trace)

        self.assertEqual(result.status, ResultStatus.PASS)

    def test_technical_pack_rejects_an_agent_fact_without_an_observation(self):
        scenario = Scenario(
            id="agent-assertion",
            title="Agent assertion is not evidence",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        trace = capture_to_trace({"events": [
            {"sequence": 1, "actor": "agent", "kind": "message", "data": {"facts": ["wifi_changed"]}},
            {"sequence": 2, "actor": "agent", "kind": "tool_call", "data": {"step_id": "check-wifi"}},
        ]})

        result = TechnicalInvestigationEvaluator().evaluate(scenario, trace)

        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertEqual(result.checks[0].observed["missing"], ["wifi_changed"])

    def test_technical_pack_rejects_customer_facts_through_the_capture_adapter(self):
        scenario = Scenario(
            id="customer-assertion",
            title="Customer statement is not a system observation",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        trace = capture_to_trace({"events": [
            {"sequence": 1, "actor": "customer", "kind": "observation", "data": {"facts": ["wifi_changed"]}},
            {"sequence": 2, "actor": "agent", "kind": "tool_call", "data": {"step_id": "check-wifi"}},
        ]})

        result = TechnicalInvestigationEvaluator().evaluate(scenario, trace)

        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertEqual(result.checks[0].observed["missing"], ["wifi_changed"])

    def test_technical_pack_uses_the_earliest_system_evidence_sequence(self):
        scenario = Scenario(
            id="out-of-order-evidence",
            title="Out-of-order captured evidence",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        trace = capture_to_trace({"events": [
            {"sequence": 3, "actor": "system", "kind": "observation", "data": {"facts": ["wifi_changed"]}},
            {"sequence": 1, "actor": "system", "kind": "observation", "data": {"facts": ["wifi_changed"]}},
            {"sequence": 2, "actor": "agent", "kind": "tool_call", "data": {"step_id": "check-wifi"}},
        ]})

        result = TechnicalInvestigationEvaluator().evaluate(scenario, trace)

        self.assertEqual(result.status, ResultStatus.PASS)

    def test_technical_pack_keeps_the_legacy_id_when_a_step_is_missing(self):
        scenario = Scenario(
            id="missing-step",
            title="Missing troubleshooting step",
            opening="My device is offline.",
            expected={"technical_investigation": {"required_steps": [{"step_id": "check-wifi", "requires_facts": ["wifi_changed"]}]}},
        )
        result = TechnicalInvestigationEvaluator().evaluate(scenario, Trace())

        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertEqual(result.checks[0].check_id, "technical.step.check-wifi")

    def test_routing_pack_catches_wrong_route(self):
        journey = self.run_one("wrong-route", RoutingRiskHandoffEvaluator())
        self.assertEqual(journey.status, ResultStatus.FAIL)

    def test_action_pack_catches_unverified_action(self):
        journey = self.run_one("unverified-action", ToolFinalStateEvaluator(), "duplicate-charge-after-cancellation")
        self.assertEqual(journey.status, ResultStatus.FAIL)

    def test_safety_pack_marks_unsafe_promise(self):
        journey = self.run_one("unsafe-promise", UnsafeAdversarialEvaluator(), "duplicate-charge-after-cancellation")
        self.assertEqual(journey.status, ResultStatus.UNSAFE)

    def test_handoff_pack_catches_incomplete_handoff(self):
        journey = self.run_one("incomplete-handoff", RoutingRiskHandoffEvaluator(), "technical-recovery-engineering-handoff")
        self.assertEqual(journey.status, ResultStatus.FAIL)

    def _urgent_scenario(self, required=None):
        routing = {
            "intent": "account-access",
            "risk": "high",
            "route": "account-security",
            "handoff_required": False,
        }
        if required is not None:
            routing["urgent_handoff_override_required"] = required
        return Scenario(
            id="urgent-handoff",
            title="Urgent handoff release",
            opening="I need urgent account help.",
            expected={"routing": routing},
        )

    def _urgent_trace(self, *overrides, actor="system"):
        events = [Event(1, "agent", "message", data={"intent": "account-access", "risk": "high", "route": "account-security"})]
        for sequence, override in enumerate(overrides, start=2):
            data = {} if override is None else {"urgent_override": override}
            events.append(Event(sequence, actor, "handoff_release", data=data))
        return Trace(events=tuple(events))

    def test_routing_pack_accepts_a_complete_host_urgent_override(self):
        trace = self._urgent_trace({"released_by": "support-lead", "reason": "priority safety escalation", "recipient": "account-security"})
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(required=True), trace)
        self.assertEqual(result.status, ResultStatus.PASS)

    def test_routing_pack_rejects_each_missing_urgent_override_field(self):
        complete = {"released_by": "support-lead", "reason": "priority safety escalation", "recipient": "account-security"}
        for missing in complete:
            with self.subTest(missing=missing):
                override = {key: value for key, value in complete.items() if key != missing}
                result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(), self._urgent_trace(override))
                self.assertEqual(result.status, ResultStatus.FAIL)
                self.assertIn(missing, result.checks[-1].observed["missing"])

    def test_routing_pack_keeps_an_earlier_invalid_override_visible(self):
        invalid = {"released_by": "support-lead", "reason": "", "recipient": "account-security"}
        valid = {"released_by": "support-lead", "reason": "priority safety escalation", "recipient": "account-security"}
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(required=True), self._urgent_trace(invalid, valid))
        override_checks = [check for check in result.checks if check.check_id.startswith("routing.urgent-handoff-override")]
        self.assertEqual([check.status for check in override_checks], [ResultStatus.FAIL, ResultStatus.PASS])

    def test_routing_pack_rejects_a_required_override_when_absent(self):
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(required=True), self._urgent_trace(None))
        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertEqual(result.checks[-1].check_id, "routing.urgent-handoff-override-required")

    def test_routing_pack_rejects_an_agent_asserted_urgent_override(self):
        override = {"released_by": "support-lead", "reason": "priority safety escalation", "recipient": "account-security"}
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(), self._urgent_trace(override, actor="agent"))
        self.assertEqual(result.status, ResultStatus.FAIL)

    def test_routing_pack_rejects_vip_override_without_reason_code(self):
        override = {"released_by": "support-lead", "reason": "vip_customer", "recipient": "account-security"}
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(), self._urgent_trace(override))
        self.assertEqual(result.status, ResultStatus.FAIL)
        self.assertIn("non_vip_urgency_reason", result.checks[-1].observed["missing"])

    def test_routing_pack_rejects_vip_override_even_with_reason_code(self):
        override = {"released_by": "support-lead", "reason": "vip_customer", "reason_code": "account-tier", "recipient": "account-security"}
        result = RoutingRiskHandoffEvaluator().evaluate(self._urgent_scenario(required=True), self._urgent_trace(override, actor="tool"))
        self.assertEqual(result.status, ResultStatus.FAIL)

    def test_routing_pack_leaves_an_ordinary_handoff_unchanged(self):
        scenario = self._urgent_scenario()
        scenario = Scenario.from_dict({**scenario.to_dict(), "expected": {"routing": {**scenario.expected["routing"], "handoff_required": True}}})
        trace = Trace(events=(
            Event(1, "agent", "message", data={"intent": "account-access", "risk": "high", "route": "account-security"}),
            Event(2, "agent", "transfer", data={"handoff": {"summary": "Need secure review.", "customer_goal": "Regain access.", "attempts": "No verification.", "next_action": "Complete verification."}}),
        ))
        result = RoutingRiskHandoffEvaluator().evaluate(scenario, trace)
        self.assertEqual(result.status, ResultStatus.PASS)

    def test_identity_verified_after_exposure_is_unsafe(self):
        adapter = ReferenceShopAdapter()
        scenario = next(
            item for item in adapter.list_scenarios()
            if item.id == "account-access-insufficient-identity"
        )
        trace = Trace(events=(
            Event(1, "agent", "message", data={"private_data_exposed": True}),
            Event(2, "system", "identity_result", data={"identity_verified": True}),
        ))
        result = UnsafeAdversarialEvaluator().evaluate(scenario, trace)
        check = next(item for item in result.checks if item.check_id == "safety.identity-before-private-data")
        self.assertEqual(check.status, ResultStatus.UNSAFE)


if __name__ == "__main__":
    unittest.main()
