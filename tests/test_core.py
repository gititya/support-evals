import unittest

from support_evals import (
    CheckResult,
    EvaluatorResult,
    Event,
    FixtureAdapter,
    Profile,
    ReleaseGate,
    ResultStatus,
    Scenario,
    Trace,
    run_suite,
)


class FixedEvaluator:
    evaluator_id = "fixed"

    def __init__(self, status):
        self.status = status

    def evaluate(self, scenario, trace):
        return EvaluatorResult(
            evaluator_id=self.evaluator_id,
            checks=(
                CheckResult(
                    check_id="fixed.check",
                    status=self.status,
                    summary="fixed test result",
                    customer_effect="test customer effect",
                ),
            ),
        )


class ErrorAdapter(FixtureAdapter):
    def run(self, scenario):
        if scenario.id == "bad":
            raise RuntimeError("adapter unavailable")
        return super().run(scenario)


class CoreContractsTests(unittest.TestCase):
    def setUp(self):
        self.scenarios = (
            Scenario(id="one", title="One", opening="Help", category="technical-support"),
            Scenario(id="bad", title="Bad", opening="Help"),
        )

    def test_scenario_round_trip_is_versioned(self):
        scenario = self.scenarios[0]
        self.assertEqual(Scenario.from_dict(scenario.to_dict()), scenario)
        with self.assertRaises(ValueError):
            Scenario.from_dict({**scenario.to_dict(), "schema_version": "9.0"})

    def test_trace_events_are_serializable(self):
        trace = Trace(events=(Event(1, "customer", "message", "Hello"),), final_state={"ok": True})
        self.assertEqual(trace.to_dict()["events"][0]["actor"], "customer")

    def test_run_retains_adapter_errors_and_denominators(self):
        profile = Profile(name="test", evaluator_ids=("fixed",), release_gate=ReleaseGate(max_errors=0))
        result = run_suite(
            ErrorAdapter(scenarios=self.scenarios),
            self.scenarios,
            profile=profile,
            evaluators=(FixedEvaluator(ResultStatus.PASS),),
        )
        self.assertEqual(result.counts.to_dict(), {
            "requested": 2,
            "completed": 1,
            "passed": 1,
            "failed": 0,
            "error": 1,
            "abstention": 0,
            "unsafe": 0,
        })
        self.assertIn("adapter unavailable", result.journeys[1].error)

    def test_statuses_preserve_unsafe_and_abstention(self):
        statuses = (ResultStatus.UNSAFE, ResultStatus.ABSTENTION)
        for status in statuses:
            profile = Profile(name="test", evaluator_ids=("fixed",), release_gate=ReleaseGate())
            result = run_suite(
                FixtureAdapter(),
                (self.scenarios[0],),
                profile=profile,
                evaluators=(FixedEvaluator(status),),
            )
            self.assertEqual(result.journeys[0].status, status)
            self.assertEqual(result.counts.to_dict()[status.value], 1)

    def test_failure_is_not_hidden_by_an_abstaining_check(self):
        class MixedEvaluator:
            evaluator_id = "mixed"

            def evaluate(self, scenario, trace):
                return EvaluatorResult(
                    evaluator_id=self.evaluator_id,
                    checks=(
                        CheckResult(
                            check_id="mixed.failed",
                            status=ResultStatus.FAIL,
                            summary="A required support step failed.",
                            customer_effect="The customer does not receive the required support outcome.",
                        ),
                        CheckResult(
                            check_id="mixed.missing-measurement",
                            status=ResultStatus.ABSTENTION,
                            summary="One optional measurement was not available.",
                            customer_effect="This part of the journey cannot be assessed.",
                        ),
                    ),
                )

        profile = Profile(
            name="test",
            evaluator_ids=("mixed",),
            release_gate=ReleaseGate(
                min_pass_rate=0.0,
                max_failed=1,
                max_abstentions=0,
            ),
        )
        result = run_suite(
            FixtureAdapter(),
            (self.scenarios[0],),
            profile=profile,
            evaluators=(MixedEvaluator(),),
        )
        self.assertEqual(result.journeys[0].status, ResultStatus.FAIL)
        self.assertEqual(result.counts.failed, 1)
        self.assertEqual(result.counts.abstention, 1)
        gate = profile.release_gate.evaluate(result)
        self.assertFalse(gate.passed)
        self.assertTrue(any("abstention" in reason for reason in gate.reasons))

    def test_profile_cannot_release_without_evaluators(self):
        with self.assertRaisesRegex(ValueError, "at least one evaluator"):
            Profile(name="no-checks", evaluator_ids=())

    def test_empty_evaluator_result_is_an_error(self):
        class EmptyEvaluator:
            evaluator_id = "empty"

            def evaluate(self, scenario, trace):
                return EvaluatorResult(evaluator_id=self.evaluator_id, checks=())

        profile = Profile(name="test", evaluator_ids=("empty",))
        result = run_suite(
            FixtureAdapter(),
            (self.scenarios[0],),
            profile=profile,
            evaluators=(EmptyEvaluator(),),
        )
        self.assertEqual(result.counts.error, 1)
        self.assertFalse(profile.release_gate.evaluate(result).passed)

    def test_release_gate_reports_every_breach(self):
        profile = Profile(name="test", evaluator_ids=("fixed",), release_gate=ReleaseGate(min_pass_rate=1.0))
        result = run_suite(
            FixtureAdapter(),
            (self.scenarios[0],),
            profile=profile,
            evaluators=(FixedEvaluator(ResultStatus.FAIL),),
        )
        gate = profile.release_gate.evaluate(result)
        self.assertFalse(gate.passed)
        self.assertGreaterEqual(len(gate.reasons), 2)

    def test_missing_evaluator_is_explicit_error(self):
        profile = Profile(name="test", evaluator_ids=("not-registered",))
        result = run_suite(FixtureAdapter(), (self.scenarios[0],), profile=profile)
        self.assertEqual(result.counts.error, 1)
        self.assertIn("missing evaluator", result.journeys[0].error)


if __name__ == "__main__":
    unittest.main()
