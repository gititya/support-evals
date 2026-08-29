import unittest

from support_evals import Event, Profile, ReleaseGate, ResultStatus, Trace, run_suite
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
