"""Public API for Support Evals."""

from .contracts import (
    Adapter,
    CheckResult,
    Event,
    Evaluator,
    EvaluatorResult,
    GateResult,
    JourneyResult,
    Profile,
    ReleaseGate,
    ResultStatus,
    RunCounts,
    RunResult,
    Scenario,
    Trace,
)
from .runner import AdapterRegistry, FixtureAdapter, default_fixture_scenarios, run_suite
from .reporting import build_report_payload, render_html, write_html, write_json
from .integrations import LangfuseExportResult, LangfuseExporter, build_langfuse_payload
from .cli import VoiceCaptureAdapter, build_registry

__all__ = [
    "Adapter",
    "AdapterRegistry",
    "CheckResult",
    "Event",
    "Evaluator",
    "EvaluatorResult",
    "FixtureAdapter",
    "GateResult",
    "JourneyResult",
    "Profile",
    "ReleaseGate",
    "ResultStatus",
    "RunCounts",
    "RunResult",
    "Scenario",
    "Trace",
    "default_fixture_scenarios",
    "run_suite",
    "build_report_payload",
    "render_html",
    "write_html",
    "write_json",
    "LangfuseExportResult",
    "LangfuseExporter",
    "build_langfuse_payload",
    "VoiceCaptureAdapter",
    "build_registry",
]
