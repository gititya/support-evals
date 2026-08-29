"""Small dependency-free command line interface for local support QA runs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import CheckResult, EvaluatorResult, Profile, ReleaseGate, ResultStatus, Scenario, Trace
from .integrations import LangfuseExporter
from .reporting import build_report_payload, write_html, write_json
from .reference import BrokenReferenceAdapter, ReferenceShopAdapter
from .runner import AdapterRegistry, FixtureAdapter, run_suite
from .packs import standard_profile, support_evaluators
from .voice import VoiceEvaluator, capture_to_trace


class FixtureOutcomeEvaluator:
    evaluator_id = "fixture-outcome"

    def evaluate(self, scenario: Scenario, trace: Trace) -> EvaluatorResult:
        outcome = trace.metadata.get("fixture_outcome", "pass")
        try:
            status = ResultStatus(str(outcome))
        except ValueError:
            status = ResultStatus.ERROR
        return EvaluatorResult(
            evaluator_id=self.evaluator_id,
            checks=(
                CheckResult(
                    check_id="fixture.outcome",
                    status=status,
                    summary=f"Fixture outcome: {outcome}",
                    customer_effect="The fixture represents the customer outcome for this test.",
                    observed=outcome,
                ),
            ),
        )


@dataclass
class VoiceCaptureAdapter:
    """Adapter for one provider-neutral captured voice journey."""

    case_path: Path
    name: str = "reference-voice"

    def __post_init__(self) -> None:
        payload = json.loads(self.case_path.read_text(encoding="utf-8"))
        self.scenario = Scenario.from_dict(payload["scenario"])
        self.trace = capture_to_trace(payload["trace"])

    def list_scenarios(self, suite: str = "default") -> tuple[Scenario, ...]:
        return (self.scenario,)

    def run(self, scenario: Scenario) -> Trace:
        if scenario.id != self.scenario.id:
            raise KeyError(f"unknown voice scenario: {scenario.id}")
        return self.trace


def build_registry(*, mutation: str | None = None, voice_case: Path | None = None) -> AdapterRegistry:
    """Return the adapters shipped with the reference release."""

    adapters: list[Any] = [FixtureAdapter(), ReferenceShopAdapter(mutation=mutation)]
    adapters.append(BrokenReferenceAdapter(mutation=mutation or "unsafe-promise"))
    if voice_case is None:
        try:
            voice_case = _voice_case_path("passing")
        except FileNotFoundError:
            voice_case = None
    if voice_case is not None and voice_case.exists():
        adapters.append(VoiceCaptureAdapter(voice_case))
    return AdapterRegistry(adapters)


def _voice_case_path(value: str) -> Path:
    requested = Path(value)
    names = [requested] if requested.suffix else [requested.with_suffix(".json")]
    roots = (Path.cwd(), Path(__file__).resolve().parents[1])
    for name in names:
        for root in roots:
            candidates = (root / name, root / "examples" / "reference_voice" / name.name)
            for candidate in candidates:
                if candidate.is_file():
                    return candidate
    raise FileNotFoundError(f"voice capture not found: {value}")


def _profile_and_evaluators(adapter_name: str) -> tuple[Profile, tuple[object, ...]]:
    if adapter_name in {"reference-shop", "reference-shop-broken"}:
        profile = standard_profile()
        return profile, support_evaluators()
    if adapter_name == "reference-voice":
        profile = Profile(
            name="voice-strict",
            evaluator_ids=("voice",),
            release_gate=ReleaseGate(
                min_pass_rate=1.0,
                max_failed=0,
                max_errors=0,
                max_abstentions=0,
                max_unsafe=0,
                require_all_completed=True,
            ),
        )
        return profile, (VoiceEvaluator(),)
    return Profile(name="fixture", evaluator_ids=("fixture-outcome",), release_gate=ReleaseGate()), (FixtureOutcomeEvaluator(),)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="support-evals")
    parser.add_argument("command", choices=("list", "plan", "run"))
    parser.add_argument("--adapter", default="fixture", help="fixture, reference-shop, reference-shop-broken, or reference-voice")
    parser.add_argument("--suite", default="default")
    parser.add_argument("--case", default="passing", help="voice capture name or path (for reference-voice)")
    parser.add_argument("--mutation", help="reference-shop defect to inject, such as unsafe-promise or wrong-route")
    parser.add_argument("--broken", action="store_true", help="use the deliberately broken reference-shop adapter")
    parser.add_argument("--output", type=Path, help="write the local JSON source-of-truth report")
    parser.add_argument("--html", "--html-output", dest="html_output", type=Path, help="write a self-contained HTML report")
    parser.add_argument("--html-trace", action="store_true", help="include full trace detail in the HTML report")
    parser.add_argument("--langfuse-dry-run", action="store_true", help="build a privacy-safe Langfuse payload without network access")
    parser.add_argument("--langfuse-output", type=Path, help="write the Langfuse dry-run payload to this JSON file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    adapter_name = "reference-shop-broken" if args.broken else args.adapter
    voice_case: Path | None = None
    if adapter_name == "reference-voice":
        try:
            voice_case = _voice_case_path(args.case)
        except FileNotFoundError as exc:
            parser.error(str(exc))
    registry = build_registry(mutation=args.mutation, voice_case=voice_case)
    try:
        adapter = registry.get(adapter_name)
    except KeyError as exc:
        parser.error(str(exc))
    scenarios = tuple(adapter.list_scenarios(args.suite))

    if args.command == "list":
        payload = {
            "adapters": list(registry.names()),
            "selected_adapter": adapter.name,
            "scenarios": [scenario.to_dict() for scenario in scenarios],
        }
        _print_or_write(payload, args.output)
        return 0
    if args.command == "plan":
        profile, evaluators = _profile_and_evaluators(adapter.name)
        payload = {
            "adapter": adapter.name,
            "suite": args.suite,
            "profile": profile.name,
            "evaluators": [evaluator.evaluator_id for evaluator in evaluators],
            "requested": len(scenarios),
            "scenarios": [{"id": scenario.id, "title": scenario.title, "category": scenario.category} for scenario in scenarios],
        }
        _print_or_write(payload, args.output)
        return 0

    profile, evaluators = _profile_and_evaluators(adapter.name)
    result = run_suite(adapter, scenarios, profile=profile, evaluators=evaluators)
    gate = profile.release_gate.evaluate(result)
    payload = build_report_payload(result, gate)
    if args.output:
        write_json(args.output, result, gate)
    if args.html_output:
        write_html(args.html_output, result, gate, include_trace=args.html_trace)

    if args.langfuse_dry_run:
        exported = LangfuseExporter().export(result, gate, dry_run=True)
        if args.langfuse_output:
            args.langfuse_output.parent.mkdir(parents=True, exist_ok=True)
            args.langfuse_output.write_text(json.dumps(exported.payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            payload["langfuse_dry_run"] = exported.payload
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if gate.passed else 1


def _print_or_write(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
