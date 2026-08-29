"""Optional Langfuse export with no SDK dependency.

Local JSON and HTML reports remain authoritative.  Export is a copy for trace
review; network failures are returned as a result and never change the local
release gate.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

from ..contracts import GateResult, RunResult


@dataclass(frozen=True)
class LangfuseExportResult:
    attempted: bool
    succeeded: bool
    dry_run: bool
    payload: dict[str, Any]
    status_code: int | None = None
    error: str | None = None


def build_langfuse_payload(
    run: RunResult,
    gate: GateResult | None = None,
    *,
    include_customer_content: bool = False,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, privacy-safe Langfuse ingestion payload.

    Scenario openings and event content are omitted unless explicitly enabled.
    This avoids sending customer text to an external service by default.
    """

    root_id = trace_id or _stable_id(run.profile, run.started_at, len(run.journeys))
    batch: list[dict[str, Any]] = []
    for index, journey in enumerate(run.journeys):
        journey_id = _stable_id(root_id, "journey", index)
        metadata = {
            "support_evals": True,
            "profile_ref": _stable_id("profile", run.profile),
            "journey_number": index + 1,
            "scenario_ref": journey_id,
            "status": journey.status.value,
            "completed": journey.completed,
        }
        if gate is not None:
            metadata["release_passed"] = gate.passed
        body: dict[str, Any] = {
            "id": journey_id,
            "name": f"support-eval:journey-{index + 1}",
            "timestamp": run.started_at or "1970-01-01T00:00:00+00:00",
            "metadata": metadata,
            "output": _journey_output(journey, include_customer_content=include_customer_content),
        }
        if include_customer_content:
            body["input"] = {
                "profile": run.profile,
                "scenario_id": journey.scenario.id,
                "category": journey.scenario.category,
                "title": journey.scenario.title,
                "opening": journey.scenario.opening,
                "events": [event.to_dict() for event in journey.trace.events] if journey.trace else [],
            }
        batch.append({"id": journey_id, "type": "trace-create", "body": body})
    return {
        "batch": batch,
        "metadata": {
            "source": "support-evals",
            "profile_ref": _stable_id("profile", run.profile),
        },
    }


class LangfuseExporter:
    """Post an optional batch to Langfuse using the standard library only."""

    def __init__(
        self,
        endpoint: str | None = None,
        public_key: str | None = None,
        secret_key: str | None = None,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/") if endpoint else None
        self.public_key = public_key
        self.secret_key = secret_key
        self.timeout = timeout

    def export(
        self,
        run: RunResult,
        gate: GateResult | None = None,
        *,
        dry_run: bool = True,
        include_customer_content: bool = False,
        trace_id: str | None = None,
    ) -> LangfuseExportResult:
        payload = build_langfuse_payload(
            run,
            gate,
            include_customer_content=include_customer_content,
            trace_id=trace_id,
        )
        if dry_run:
            return LangfuseExportResult(True, True, True, payload)
        if not self.endpoint or not self.public_key or not self.secret_key:
            return LangfuseExportResult(
                attempted=False,
                succeeded=False,
                dry_run=False,
                payload=payload,
                error="Langfuse endpoint, public key, and secret key are required for export",
            )
        request = urllib.request.Request(
            self._ingestion_url(),
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={
                "Authorization": "Basic " + base64.b64encode(f"{self.public_key}:{self.secret_key}".encode()).decode(),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status_code = getattr(response, "status", None)
                if status_code is None:
                    status_code = response.getcode()
                if not 200 <= status_code < 300:
                    return LangfuseExportResult(True, False, False, payload, status_code, f"Langfuse returned HTTP {status_code}")
                return LangfuseExportResult(True, True, False, payload, status_code)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return LangfuseExportResult(True, False, False, payload, error=str(exc))

    def _ingestion_url(self) -> str:
        endpoint = self.endpoint or ""
        return endpoint if endpoint.endswith("/api/public/ingestion") else endpoint + "/api/public/ingestion"


def _stable_id(*parts: Any) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "support-evals:" + ":".join(map(str, parts))))


def _journey_output(journey: Any, *, include_customer_content: bool) -> dict[str, Any]:
    """Keep externally exported output free of customer text by default."""

    if include_customer_content:
        return {
            "status": journey.status.value,
            "error": journey.error,
            "evaluators": [result.to_dict() for result in journey.evaluators],
        }
    return {
        "status": journey.status.value,
        "error_present": bool(journey.error),
        "evaluators": [
            {
                "evaluator_number": evaluator_index + 1,
                "status": result.status.value,
                "checks": [
                    {
                        "check_number": check_index + 1,
                        "status": check.status.value,
                        "evidence_count": len(check.evidence),
                        "error_present": bool(check.error),
                    }
                    for check_index, check in enumerate(result.checks)
                ],
            }
            for evaluator_index, result in enumerate(journey.evaluators)
        ],
    }
