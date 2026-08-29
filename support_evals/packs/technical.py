"""Deterministic checks for evidence-led technical troubleshooting."""

from __future__ import annotations

from ..contracts import EvaluatorResult, Scenario, Trace
from ._common import agent_events, check, expected_map, result, values


class TechnicalInvestigationEvaluator:
    evaluator_id = "technical-investigation"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        expected = expected_map(scenario, "technical_investigation")
        checks = []
        evidence_sequences: dict[str, int] = {}
        for event in trace.events:
            for fact in values(event, "facts"):
                evidence_sequences.setdefault(fact, event.sequence)

        agent = agent_events(trace)
        recorded_steps = {
            str(event.data.get("step_id")): event
            for event in agent
            if event.data.get("step_id")
        }
        for item in expected.get("required_steps", ()):
            if isinstance(item, str):
                item = {"step_id": item}
            step_id = str(item.get("step_id"))
            step = recorded_steps.get(step_id)
            requirements = [str(value) for value in item.get("requires_facts", ())]
            missing = [fact for fact in requirements if fact not in evidence_sequences]
            premature = [
                fact for fact in requirements
                if fact in evidence_sequences and step is not None and evidence_sequences[fact] >= step.sequence
            ]
            passed = step is not None and not missing and not premature
            details = []
            if step is None:
                details.append("step not recorded")
            if missing:
                details.append(f"missing evidence: {', '.join(missing)}")
            if premature:
                details.append(f"used before evidence: {', '.join(premature)}")
            checks.append(
                check(
                    f"technical.step.{step_id}",
                    passed,
                    f"Troubleshooting step {step_id} {'followed the available evidence' if passed else 'was not evidence-led'}"
                    + (f" ({'; '.join(details)})." if details else "."),
                    "The customer is guided through a relevant next step based on what support has learned."
                    if passed
                    else "The customer may be sent through irrelevant steps or receive a premature diagnosis, adding time and effort.",
                    evidence=[f"step sequence: {step.sequence if step else None}", f"evidence sequences: {evidence_sequences}"],
                    expected={"step_id": step_id, "requires_facts": requirements},
                    observed={"step_sequence": step.sequence if step else None, "missing": missing, "premature": premature},
                )
            )

        required_conclusions = [str(item) for item in expected.get("required_conclusions", ())]
        used_conclusions = set().union(*(values(event, "conclusions") for event in agent))
        for conclusion in required_conclusions:
            present = conclusion in used_conclusions
            checks.append(
                check(
                    f"technical.conclusion.{conclusion}",
                    present,
                    f"Investigation conclusion {'is' if present else 'is not'} supported: {conclusion}.",
                    "The customer gets a clear explanation of what support found."
                    if present
                    else "The customer may be left with no reliable explanation or next step.",
                    evidence=[f"recorded conclusions: {sorted(used_conclusions)}"],
                    expected=conclusion,
                    observed=sorted(used_conclusions),
                )
            )
        if not checks:
            checks.append(check(
                "technical.trace-present", bool(trace.events),
                "Technical trace is present." if trace.events else "Technical trace is empty.",
                "The customer has a recorded support journey." if trace.events else "The customer journey cannot be reviewed.",
                evidence=[f"event count: {len(trace.events)}"], observed=len(trace.events),
            ))
        return result(self.evaluator_id, checks, "Evidence timing and technical investigation checks.")


EvidenceTimedTechnicalEvaluator = TechnicalInvestigationEvaluator
