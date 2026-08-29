import unittest
from unittest.mock import patch
import urllib.error

from support_evals import (
    CheckResult,
    EvaluatorResult,
    FixtureAdapter,
    Profile,
    ReleaseGate,
    ResultStatus,
    Scenario,
    run_suite,
)
from support_evals.cli import FixtureOutcomeEvaluator
from support_evals.integrations import LangfuseExporter, build_langfuse_payload


class LangfuseExportTests(unittest.TestCase):
    def _run(self):
        adapter = FixtureAdapter()
        scenarios = adapter.list_scenarios()
        profile = Profile(name="privacy-test", evaluator_ids=("fixture-outcome",), release_gate=ReleaseGate())
        run = run_suite(adapter, scenarios, profile=profile, evaluators=(FixtureOutcomeEvaluator(),))
        return run, profile.release_gate.evaluate(run)

    def test_payload_omits_customer_content_by_default(self):
        run, gate = self._run()
        payload = build_langfuse_payload(run, gate, trace_id="fixed")
        encoded = str(payload)
        self.assertNotIn("I cannot sign in to my account.", encoded)
        self.assertNotIn('"content"', encoded)
        self.assertEqual(payload["batch"][0]["body"]["id"], payload["batch"][0]["body"]["id"])

    def test_privacy_safe_payload_uses_opaque_scenario_reference(self):
        private_value = "customer-email@example.com"

        class PrivateNamedEvaluator:
            evaluator_id = private_value

            def evaluate(self, scenario, trace):
                return EvaluatorResult(
                    evaluator_id=self.evaluator_id,
                    checks=(CheckResult(
                        check_id=private_value,
                        status=ResultStatus.PASS,
                        summary=private_value,
                        customer_effect=private_value,
                        evidence=(private_value,),
                    ),),
                )

        adapter = FixtureAdapter(scenarios=(
            Scenario(
                id=private_value,
                title=private_value,
                opening=private_value,
                category=private_value,
            ),
        ))
        profile = Profile(name=private_value, evaluator_ids=(private_value,))
        run = run_suite(
            adapter,
            adapter.list_scenarios(),
            profile=profile,
            evaluators=(PrivateNamedEvaluator(),),
        )
        encoded = str(build_langfuse_payload(run, profile.release_gate.evaluate(run), trace_id="fixed"))
        self.assertNotIn(private_value, encoded)
        self.assertIn("scenario_ref", encoded)

    def test_dry_run_returns_payload_without_network(self):
        run, gate = self._run()
        exporter = LangfuseExporter("https://example.invalid", "public", "secret")
        with patch("urllib.request.urlopen") as urlopen:
            result = exporter.export(run, gate, dry_run=True, trace_id="fixed")
        urlopen.assert_not_called()
        self.assertTrue(result.attempted)
        self.assertTrue(result.succeeded)
        self.assertTrue(result.dry_run)

    def test_export_failure_is_isolated(self):
        run, gate = self._run()
        exporter = LangfuseExporter("https://example.invalid", "public", "secret")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            result = exporter.export(run, gate, dry_run=False, trace_id="fixed")
        self.assertTrue(result.attempted)
        self.assertFalse(result.succeeded)
        self.assertIn("offline", result.error)
        # Export returns a copy result; it does not mutate the local gate.
        self.assertTrue(gate.passed)


if __name__ == "__main__":
    unittest.main()
