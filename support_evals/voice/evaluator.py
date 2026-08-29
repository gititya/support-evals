"""Deterministic checks for captured customer-support voice journeys."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..contracts import CheckResult, Event, EvaluatorResult, ResultStatus, Scenario, Trace


class VoiceEvaluator:
    """Evaluate voice meaning, turn-taking, timing, actions, and handoffs.

    Adapters normalize their provider's trace into :class:`~support_evals.Trace`
    events.  The evaluator reads explicit event metadata where available and
    never treats a missing signal as a successful live-call observation.
    """

    evaluator_id = "voice"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        expected = _voice_expectations(scenario)
        checks = (
            _check_critical_meaning(expected, trace),
            _check_response_latency(expected, trace),
            _check_interruption_yield(expected, trace),
            _check_silence_budget(expected, trace),
            _check_repeated_information(expected, trace),
            _check_support_action(expected, trace),
            _check_final_state(expected, trace),
            _check_handoff(expected, trace),
        )
        status = _status_word(checks)
        return EvaluatorResult(
            evaluator_id=self.evaluator_id,
            checks=checks,
            summary=f"Voice journey {status}; evidence is a captured trace, not a live call.",
        )


def evaluate_voice_trace(scenario: Scenario, trace: Trace) -> EvaluatorResult:
    """Convenience function for callers that do not need to retain an evaluator."""

    return VoiceEvaluator().evaluate(scenario, trace)


def _voice_expectations(scenario: Scenario) -> Mapping[str, Any]:
    value = scenario.expected.get("voice", scenario.expected)
    return value if isinstance(value, Mapping) else {}


def _events(trace: Trace, *, actor: str | None = None) -> list[Event]:
    events = sorted(trace.events, key=lambda event: event.sequence)
    if actor is not None:
        events = [event for event in events if event.actor.casefold() == actor.casefold()]
    return events


def _kind(event: Event, *names: str) -> bool:
    value = event.kind.casefold().replace("-", "_").replace(" ", "_")
    return value in {name.casefold().replace("-", "_").replace(" ", "_") for name in names}


def _data(event: Event, *keys: str) -> Any:
    for key in keys:
        if key in event.data:
            return event.data[key]
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _check_critical_meaning(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    entities = expected.get("critical_entities", expected.get("required_entities", {}))
    negations = expected.get("critical_negations", expected.get("required_negations", ()))
    if not isinstance(entities, Mapping):
        entities = {}
    if isinstance(negations, Mapping):
        negations = [key if value else f"not {key}" for key, value in negations.items()]
    negations = tuple(str(value) for value in negations) if isinstance(negations, (list, tuple, set)) else ()
    if not entities and not negations:
        return _abstain(
            "voice.critical_meaning",
            "No critical entities or negations were declared for this journey.",
            "The trace does not define which customer facts must survive the call.",
        )

    agent_events = [
        event
        for event in _events(trace)
        if event.actor.casefold() in {"agent", "assistant", "bot"}
        and (_kind(event, "message", "speech", "speech_start", "speech_end", "final", "handoff"))
    ]
    observed_entities: dict[str, Any] = {}
    observed_negations: set[str] = set()
    text = " ".join(event.content.casefold() for event in agent_events)
    for event in agent_events:
        event_entities = _data(event, "entities", "critical_entities")
        if isinstance(event_entities, Mapping):
            observed_entities.update(event_entities)
        event_negations = _data(event, "negations", "critical_negations")
        if isinstance(event_negations, (list, tuple, set)):
            observed_negations.update(str(value).casefold() for value in event_negations)

    missing: list[str] = []
    wrong: list[str] = []
    for key, value in entities.items():
        if key in observed_entities:
            if str(observed_entities[key]).casefold() != str(value).casefold():
                wrong.append(f"{key} was stated as {observed_entities[key]!r}, not {value!r}")
        elif str(value).casefold() not in text:
            missing.append(f"{key}={value}")
    for phrase in negations:
        normalized = phrase.casefold()
        if normalized not in observed_negations and normalized not in text:
            missing.append(f"negation {phrase!r}")
    if missing or wrong:
        problems = "; ".join(wrong + [f"missing {item}" for item in missing])
        return _fail(
            "voice.critical_meaning",
            f"The agent did not preserve a critical customer fact: {problems}.",
            "The customer may be misunderstood, asked to correct the record again, or sent through the wrong support path.",
            expected={"entities": dict(entities), "negations": list(negations)},
            observed={"entities": observed_entities, "negations": sorted(observed_negations)},
        )
    return _pass(
        "voice.critical_meaning",
        "The agent preserved the declared customer facts and negations.",
        expected={"entities": dict(entities), "negations": list(negations)},
        observed={"entities": observed_entities, "negations": sorted(observed_negations)},
    )


def _check_response_latency(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    limit = _number(expected.get("max_response_latency_ms", expected.get("response_latency_budget_ms")))
    latencies: list[float] = []
    for event in _events(trace):
        value = _number(_data(event, "response_latency_ms", "latency_ms", "end_of_speech_to_response_ms"))
        if value is not None:
            latencies.append(value)
    if not latencies:
        customer_ends = [event for event in _events(trace) if event.actor.casefold() == "customer" and _kind(event, "speech_end", "message_end")]
        agent_starts = [event for event in _events(trace) if event.actor.casefold() in {"agent", "assistant", "bot"} and _kind(event, "speech_start", "message", "speech")]
        for customer_end in customer_ends:
            end = _timestamp(customer_end, "end_ms", "timestamp_ms", "time_ms", "timestamp")
            following = [event for event in agent_starts if (_timestamp(event, "start_ms", "timestamp_ms", "time_ms", "timestamp") or -1) >= (end or 0)]
            if end is not None and following:
                start = _timestamp(following[0], "start_ms", "timestamp_ms", "time_ms", "timestamp")
                if start is not None:
                    latencies.append(start - end)
    if not latencies:
        return _abstain(
            "voice.response_latency",
            "Response latency was not recorded in the captured trace.",
            "The team cannot tell whether callers waited too long after they finished speaking.",
        )
    observed = max(latencies)
    if limit is not None and observed > limit:
        return _fail(
            "voice.response_latency",
            f"The slowest response took {observed:.0f} ms, over the {limit:.0f} ms budget.",
            "Long gaps make callers think the line failed and can cause them to repeat themselves or hang up.",
            expected=limit,
            observed=observed,
        )
    summary = f"All recorded responses stayed within {limit:.0f} ms." if limit is not None else "Response latency was recorded."
    return _pass("voice.response_latency", summary, expected=limit, observed=observed)


def _check_interruption_yield(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    interruptions = [event for event in _events(trace) if _kind(event, "interruption", "barge_in", "customer_interrupt")]
    required = bool(expected.get("require_interruption_yield", True))
    if not interruptions:
        return _pass("voice.interruption_yield", "No customer interruption occurred in this trace.", expected=required, observed=False)
    bad: list[str] = []
    missing: list[str] = []
    for event in interruptions:
        yielded = _data(event, "yielded", "agent_yielded", "stopped", "turn_yielded")
        if yielded is None:
            missing.append(f"event {event.sequence}")
        elif yielded is False or (isinstance(yielded, str) and yielded.casefold() in {"false", "no", "0"}):
            bad.append(f"event {event.sequence}")
    if bad and required:
        return _fail(
            "voice.interruption_yield",
            f"The agent kept speaking after the caller interrupted ({', '.join(bad)}).",
            "Callers cannot correct a wrong assumption and may hear instructions that no longer apply.",
            expected=True,
            observed={"interruptions": len(interruptions), "failed_events": bad},
        )
    if missing and required:
        return _abstain(
            "voice.interruption_yield",
            f"The trace did not record whether the agent yielded ({', '.join(missing)}).",
            "The team cannot tell whether callers were able to correct the agent.",
        )
    return _pass("voice.interruption_yield", "The agent yielded when the caller interrupted.", expected=required, observed={"interruptions": len(interruptions)})


def _check_silence_budget(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    limit = _number(expected.get("max_silence_ms", expected.get("silence_budget_ms")))
    silence = [_number(_data(event, "duration_ms", "silence_ms", "length_ms")) for event in _events(trace) if _kind(event, "silence", "silence_gap", "no_audio")]
    values = [value for value in silence if value is not None]
    if not values:
        return _abstain("voice.silence_budget", "Silence duration was not recorded in the captured trace.", "The team cannot tell whether callers experienced an unexplained dead-air gap.")
    observed = max(values)
    if limit is not None and observed > limit:
        return _fail("voice.silence_budget", f"Silence reached {observed:.0f} ms, over the {limit:.0f} ms budget.", "Dead air makes callers unsure whether the agent is still working and increases hang-ups.", expected=limit, observed=observed)
    return _pass("voice.silence_budget", "Recorded silence stayed within the budget.", expected=limit, observed=observed)


def _check_repeated_information(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    limit = int(_number(expected.get("max_customer_repetitions", expected.get("max_repeated_customer_information", 0))) or 0)
    repetitions = _number(trace.metadata.get("customer_repetitions", trace.metadata.get("repeated_customer_information")))
    if repetitions is None:
        repetitions = sum(1 for event in _events(trace, actor="customer") if bool(_data(event, "repeated", "customer_repeat", "repeated_information", "repeat")))
    if repetitions > limit:
        return _fail("voice.repeated_customer_information", f"The caller repeated information {repetitions:.0f} time(s), over the limit of {limit}.", "Repeated questions increase effort and make the caller feel that the support agent is not listening.", expected=limit, observed=repetitions)
    return _pass("voice.repeated_customer_information", f"The caller did not exceed the {limit}-repeat limit.", expected=limit, observed=repetitions)


def _check_support_action(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    action = expected.get("expected_action", expected.get("required_action"))
    if action is None:
        return _abstain("voice.support_action", "No expected support action was declared.", "The trace does not say which technical-support step should have happened.")
    action_name = str(action.get("name", action.get("action", action))) if isinstance(action, Mapping) else str(action)
    calls = [event for event in _events(trace) if _kind(event, "tool_call", "tool_result", "action", "action_result", "support_action")]
    matching = [event for event in calls if _event_action_name(event) == action_name or action_name.casefold() in event.content.casefold()]
    if not matching:
        return _fail("voice.support_action", f"The expected support action {action_name!r} was not recorded.", "The customer may be left with the same fault or told that it was fixed when no recovery step ran.", expected=action_name, observed=[event.content for event in calls])
    if isinstance(action, Mapping) and action.get("success", True):
        outcomes = [_data(event, "success", "succeeded", "ok") for event in matching]
        successful = any(
            value is True or (isinstance(value, str) and value.casefold() in {"true", "yes", "1"})
            for value in outcomes
        )
        if not successful and all(value is None for value in outcomes):
            return _abstain(
                "voice.support_action",
                f"The action {action_name!r} was called, but the trace did not record whether it succeeded.",
                "The team cannot confirm that the customer's problem changed after the support action.",
            )
        if not successful:
            return _fail("voice.support_action", f"The support action {action_name!r} was recorded but did not succeed.", "The technical problem remains unresolved even though the call appears to have taken action.", expected=action, observed=[dict(event.data) for event in matching])
    return _pass("voice.support_action", f"The expected support action {action_name!r} was recorded.", expected=action, observed=[dict(event.data) for event in matching])


def _check_final_state(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    wanted = expected.get("expected_final_state", expected.get("final_state"))
    if not isinstance(wanted, Mapping) or not wanted:
        return _abstain("voice.final_state", "No expected final support state was declared.", "The run cannot verify whether the customer's technical problem was actually resolved.")
    missing = [key for key, value in wanted.items() if trace.final_state.get(key) != value]
    if missing:
        return _fail("voice.final_state", f"The final support state did not match: {', '.join(missing)}.", "The customer's issue was not verified as resolved, so they may need to call again.", expected=dict(wanted), observed=dict(trace.final_state))
    return _pass("voice.final_state", "The final support state matched the expected outcome.", expected=dict(wanted), observed=dict(trace.final_state))


def _check_handoff(expected: Mapping[str, Any], trace: Trace) -> CheckResult:
    required = bool(expected.get("handoff_required", expected.get("requires_handoff", False)))
    handoffs = [event for event in _events(trace) if _kind(event, "handoff", "transfer")]
    if required and not handoffs:
        return _fail("voice.safe_handoff", "The journey needed a human handoff, but no handoff was recorded.", "The caller can be stranded without a clear next owner when automation cannot safely resolve the issue.", expected=True, observed=False)
    if not handoffs:
        return _pass("voice.safe_handoff", "No handoff was required for this resolved journey.", expected=required, observed=False)
    required_fields = expected.get("handoff_required_fields", ("summary", "reason"))
    missing: list[str] = []
    for field in required_fields if isinstance(required_fields, (list, tuple, set)) else ():
        if not any(_data(event, str(field)) not in (None, "", []) for event in handoffs):
            missing.append(str(field))
    unsafe = any(_data(event, "safe", "complete") is False for event in handoffs)
    if missing or unsafe:
        detail = f"missing {', '.join(missing)}" if missing else "marked unsafe"
        return _fail("voice.safe_handoff", f"The handoff was incomplete ({detail}).", "The next support person will lack the facts needed to help, forcing the caller to repeat the issue or causing a missed escalation.", expected=list(required_fields) if isinstance(required_fields, (list, tuple, set)) else [], observed=[dict(event.data) for event in handoffs])
    return _pass("voice.safe_handoff", "The handoff contained the required support context.", expected=list(required_fields) if isinstance(required_fields, (list, tuple, set)) else [], observed=[dict(event.data) for event in handoffs])


def _timestamp(event: Event, *keys: str) -> float | None:
    return _number(_data(event, *keys))


def _event_action_name(event: Event) -> str:
    value = _data(event, "name", "action", "tool", "type")
    if isinstance(value, Mapping):
        value = value.get("name", value.get("action", value.get("type", "")))
    return str(value or "")


def _pass(check_id: str, summary: str, *, expected: Any = None, observed: Any = None) -> CheckResult:
    evidence = _evidence(expected, observed)
    return CheckResult(check_id, ResultStatus.PASS, summary, "No customer effect identified.", evidence=evidence, expected=expected, observed=observed)


def _fail(check_id: str, summary: str, effect: str, *, expected: Any = None, observed: Any = None) -> CheckResult:
    evidence = _evidence(expected, observed)
    return CheckResult(check_id, ResultStatus.FAIL, summary, effect, evidence=evidence, expected=expected, observed=observed)


def _abstain(check_id: str, summary: str, effect: str) -> CheckResult:
    return CheckResult(check_id, ResultStatus.ABSTENTION, summary, effect)


def _evidence(expected: Any, observed: Any) -> tuple[str, ...]:
    evidence = []
    if expected is not None:
        evidence.append(f"expected: {expected!r}")
    if observed is not None:
        evidence.append(f"observed: {observed!r}")
    return tuple(evidence)


def _status_word(checks: tuple[CheckResult, ...]) -> str:
    return "passed" if all(check.status is ResultStatus.PASS for check in checks) else "needs review"
