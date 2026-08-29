import tempfile
import unittest
from pathlib import Path

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
from support_evals.reporting import render_html, write_html, write_json


class ReportingTests(unittest.TestCase):
    def _run(self, status=ResultStatus.PASS):
        class Evaluator:
            evaluator_id = "test"

            def evaluate(self, scenario, trace):
                return EvaluatorResult(
                    evaluator_id=self.evaluator_id,
                    checks=(CheckResult(
                        check_id="answer.<check>",
                        status=status,
                        summary="Observed <summary>",
                        customer_effect="Customer sees <effect>",
                        evidence=("Evidence <one>",),
                        error="bad <error>" if status is ResultStatus.ERROR else None,
                    ),),
                )

        scenario = Scenario(id="case<1>", title="Cannot <sign in>", opening="Help <me>", category="technical-support")
        profile = Profile(name="support <default>", evaluator_ids=("test",), release_gate=ReleaseGate())
        return run_suite(
            FixtureAdapter(scenarios=(scenario,)), (scenario,), profile=profile, evaluators=(Evaluator(),)
        ), profile

    def test_html_escapes_untrusted_fields_and_shows_denominators(self):
        run, profile = self._run(ResultStatus.FAIL)
        html = render_html(run, profile.release_gate.evaluate(run))
        self.assertIn("Cannot &lt;sign in&gt;", html)
        self.assertNotIn("Cannot <sign in>", html)
        self.assertIn("0 / 1", html)
        self.assertIn("Requested journeys", html)
        self.assertIn("Customer sees &lt;effect&gt;", html)
        self.assertIn("Evidence &lt;one&gt;", html)

    def test_unsafe_and_error_are_visible(self):
        run, profile = self._run(ResultStatus.UNSAFE)
        unsafe_html = render_html(run, profile.release_gate.evaluate(run))
        self.assertIn("UNSAFE", unsafe_html)
        self.assertIn("Customer sees &lt;effect&gt;", unsafe_html)

        error_run, error_profile = self._run(ResultStatus.ERROR)
        error_html = render_html(error_run, error_profile.release_gate.evaluate(error_run))
        self.assertIn("ERROR", error_html)
        self.assertIn("Errors", error_html)
        self.assertIn("bad &lt;error&gt;", error_html)

    def test_trace_is_optional_in_html_but_present_in_local_json(self):
        run, profile = self._run()
        run = run.__class__(
            profile=run.profile,
            journeys=tuple(
                journey.__class__(
                    scenario=journey.scenario,
                    completed=journey.completed,
                    trace=Trace(events=(Event(1, "customer", "message", "secret customer text"),)),
                    evaluators=journey.evaluators,
                    error=journey.error,
                )
                for journey in run.journeys
            ),
        )
        gate = profile.release_gate.evaluate(run)
        self.assertNotIn("secret customer text", render_html(run, gate))
        self.assertIn("secret customer text", render_html(run, gate, include_trace=True))
        with tempfile.TemporaryDirectory() as directory:
            json_path = write_json(Path(directory) / "report.json", run, gate)
            self.assertIn("secret customer text", json_path.read_text(encoding="utf-8"))
            html_path = write_html(Path(directory) / "report.html", run, gate)
            self.assertTrue(html_path.exists())


if __name__ == "__main__":
    unittest.main()
