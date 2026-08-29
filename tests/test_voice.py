import json
import unittest
from pathlib import Path

from support_evals import Event, Scenario, Trace
from support_evals.contracts import ResultStatus
from support_evals.voice import VoiceEvaluator, capture_to_trace


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "examples" / "reference_voice"


def load_case(name: str):
    value = json.loads((FIXTURES / name).read_text())
    return Scenario.from_dict(value["scenario"]), capture_to_trace(value["trace"])


class VoicePackTests(unittest.TestCase):
    def evaluate(self, name: str):
        scenario, trace = load_case(name)
        return VoiceEvaluator().evaluate(scenario, trace)

    def checks(self, result):
        return {check.check_id: check for check in result.checks}

    def test_reference_journey_passes(self):
        result = self.evaluate("passing.json")
        self.assertEqual(result.status, ResultStatus.PASS)
        self.assertTrue(all(check.status is ResultStatus.PASS for check in result.checks))

    def test_catches_lost_date_or_account_fact(self):
        checks = self.checks(self.evaluate("broken-hearing.json"))
        self.assertEqual(checks["voice.critical_meaning"].status, ResultStatus.FAIL)
        self.assertTrue(checks["voice.critical_meaning"].customer_effect)

    def test_catches_slow_end_of_speech_response(self):
        checks = self.checks(self.evaluate("broken-timing.json"))
        self.assertEqual(checks["voice.response_latency"].status, ResultStatus.FAIL)
        self.assertIn("caller", checks["voice.response_latency"].customer_effect)

    def test_catches_failure_to_yield_after_interruption(self):
        checks = self.checks(self.evaluate("broken-interruption.json"))
        self.assertEqual(checks["voice.interruption_yield"].status, ResultStatus.FAIL)
        self.assertTrue(checks["voice.interruption_yield"].customer_effect)

    def test_catches_silence_and_repetition(self):
        checks = self.checks(self.evaluate("broken-silence-repeat.json"))
        self.assertEqual(checks["voice.silence_budget"].status, ResultStatus.FAIL)
        self.assertEqual(checks["voice.repeated_customer_information"].status, ResultStatus.FAIL)

    def test_catches_missing_support_action(self):
        checks = self.checks(self.evaluate("broken-action.json"))
        self.assertEqual(checks["voice.support_action"].status, ResultStatus.FAIL)
        self.assertTrue(checks["voice.support_action"].customer_effect)

    def test_catches_wrong_final_outcome(self):
        checks = self.checks(self.evaluate("broken-outcome.json"))
        self.assertEqual(checks["voice.final_state"].status, ResultStatus.FAIL)
        self.assertTrue(checks["voice.final_state"].customer_effect)

    def test_import_boundary_keeps_provider_data_under_event_data(self):
        trace = capture_to_trace({"events": [{"sequence": 1, "actor": "customer", "kind": "speech_end", "content": "hello", "data": {"vendor": "eva"}}]})
        self.assertEqual(trace.events[0].data["vendor"], "eva")

    def test_missing_interruption_result_does_not_pass(self):
        scenario, trace = load_case("passing.json")
        events = tuple(
            Event(event.sequence, event.actor, event.kind, event.content, {})
            if event.kind == "interruption"
            else event
            for event in trace.events
        )
        result = VoiceEvaluator().evaluate(
            scenario,
            Trace(events=events, final_state=trace.final_state, metadata=trace.metadata),
        )
        self.assertEqual(self.checks(result)["voice.interruption_yield"].status, ResultStatus.ABSTENTION)

    def test_action_call_without_success_result_does_not_pass(self):
        scenario, trace = load_case("passing.json")
        events = tuple(
            Event(
                event.sequence,
                event.actor,
                event.kind,
                event.content,
                {key: value for key, value in event.data.items() if key != "success"},
            )
            if event.kind == "tool_call" and event.data.get("name") == "reconnect_camera"
            else event
            for event in trace.events
        )
        result = VoiceEvaluator().evaluate(
            scenario,
            Trace(events=events, final_state=trace.final_state, metadata=trace.metadata),
        )
        self.assertEqual(self.checks(result)["voice.support_action"].status, ResultStatus.ABSTENTION)


if __name__ == "__main__":
    unittest.main()
