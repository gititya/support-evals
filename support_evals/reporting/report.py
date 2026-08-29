"""Human-readable local reports.

The JSON payload is the local source of truth.  HTML is a presentation of that
payload for support leaders and keeps every requested case visible, including
errors, abstentions, and unsafe outcomes.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from ..contracts import GateResult, JourneyResult, ResultStatus, RunResult


def build_report_payload(
    run: RunResult,
    gate: GateResult | None = None,
    *,
    include_trace: bool = True,
) -> dict[str, Any]:
    """Return the complete local report payload.

    ``include_trace`` is true for local JSON by default because it is the
    evidence record.  Callers producing a smaller handoff can opt out.
    """

    payload = run.to_dict(include_trace=include_trace)
    payload["release_gate"] = gate.to_dict() if gate is not None else None
    payload["evidence"] = {
        "source": "local Support Evals run",
        "validation": "production-shaped and locally tested; not production-validated",
    }
    return payload


def write_json(
    path: str | Path,
    run: RunResult,
    gate: GateResult | None = None,
    *,
    include_trace: bool = True,
) -> Path:
    """Write the local source-of-truth report and return its path."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_report_payload(run, gate, include_trace=include_trace), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return destination


def render_html(
    run: RunResult,
    gate: GateResult | None = None,
    *,
    include_trace: bool = False,
) -> str:
    """Render a self-contained accessible HTML report.

    Trace content is deliberately hidden unless the caller asks for it.  The
    default report still shows check evidence and customer effect, which are
    the most useful review fields for a support leader.
    """

    payload = build_report_payload(run, gate, include_trace=include_trace)
    counts = run.counts
    pass_rate = counts.passed / counts.requested if counts.requested else 0.0
    verdict = "READY TO RELEASE" if gate is not None and gate.passed else "DO NOT RELEASE"
    verdict_class = "pass" if gate is not None and gate.passed else "unsafe"
    gate_reasons = tuple(gate.reasons) if gate is not None else ("No release decision was supplied.",)
    journey_cards = "\n".join(_journey_card(journey, include_trace=include_trace) for journey in run.journeys)
    risks = _risk_items(run)
    risk_markup = "\n".join(f"<li>{_esc(item)}</li>" for item in risks)
    if not risk_markup:
        risk_markup = "<li>No unsafe journey or failed check was recorded.</li>"
    reason_markup = "\n".join(f"<li>{_esc(reason)}</li>" for reason in gate_reasons)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Support Evals — {_esc(run.profile)}</title>
  <style>
    :root {{ color-scheme: dark; --bg:#171411; --surface:#211d19; --surface-2:#2b2520; --text:#f3eee7; --muted:#c6bbae; --line:#554a40; --good:#8ed3a9; --bad:#ff9c8a; --warn:#f0cc7a; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ max-width:1100px; margin:0 auto; padding:32px 20px 64px; }}
    h1,h2,h3 {{ line-height:1.2; }} h1 {{ font-size:clamp(1.8rem,4vw,3rem); margin:0; }} h2 {{ margin-top:2rem; }}
    .eyebrow {{ color:var(--muted); font:0.78rem/1.2 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.12em; text-transform:uppercase; }}
    .lede {{ color:var(--muted); max-width:70ch; }}
    .verdict {{ display:inline-block; border:1px solid var(--line); border-radius:8px; padding:10px 14px; font-weight:700; letter-spacing:.04em; }}
    .verdict.pass {{ color:var(--good); border-color:var(--good); }} .verdict.unsafe {{ color:var(--bad); border-color:var(--bad); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:10px; margin:22px 0; }}
    .metric, article {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; }}
    .metric {{ padding:14px; }} .metric strong {{ display:block; font-size:1.5rem; }} .metric span {{ color:var(--muted); }}
    article {{ padding:18px; margin:12px 0; }} article header {{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:8px; }}
    .status {{ font:700 .8rem ui-monospace,SFMono-Regular,Menlo,monospace; text-transform:uppercase; }}
    .status-pass {{ color:var(--good); }} .status-fail,.status-unsafe,.status-error {{ color:var(--bad); }} .status-abstention {{ color:var(--warn); }}
    .meta,.muted {{ color:var(--muted); }} .meta {{ font-size:.92rem; }}
    ul {{ padding-left:1.25rem; }} li {{ margin:.35rem 0; }} code {{ color:var(--warn); }}
    details {{ margin-top:14px; border-top:1px solid var(--line); padding-top:12px; }} summary {{ cursor:pointer; color:var(--muted); }}
    .check {{ border-left:3px solid var(--line); padding-left:12px; margin:14px 0; }} .check h4 {{ margin:.1rem 0; }}
    .check p {{ margin:.25rem 0; }} .label {{ color:var(--muted); font-size:.85rem; }}
    .notice {{ color:var(--muted); font-size:.92rem; }}
    a {{ color:var(--warn); }} :focus-visible {{ outline:3px solid var(--warn); outline-offset:3px; }}
  </style>
</head>
<body>
<main>
  <p class="eyebrow">Support Evals · local evidence report</p>
  <h1>{_esc(run.profile)}</h1>
  <p><span class="verdict {verdict_class}">{verdict}</span></p>
  <p class="lede">This report shows how the tested support agent handled complete customer journeys. It is based on a local run, not production customer traffic.</p>

  <section aria-labelledby="summary"><h2 id="summary">Run summary</h2>
    <div class="grid">
      {_metric("Requested journeys", f"{counts.requested}", "denominator")}
      {_metric("Passed", f"{counts.passed} / {counts.requested}", f"{pass_rate:.1%} pass rate")}
      {_metric("Failed", str(counts.failed), "journeys")}
      {_metric("Unsafe", str(counts.unsafe), "journeys")}
      {_metric("Errors", str(counts.error), "execution or evaluation")}
      {_metric("Abstentions", str(counts.abstention), "not judged")}
    </div>
    <p class="notice">Every requested journey remains in the denominator, including journeys that did not complete or produced an error. One journey can appear in more than one risk count when it contains several kinds of problem.</p>
  </section>

  <section aria-labelledby="gate"><h2 id="gate">Release decision</h2><ul>{reason_markup}</ul></section>

  <section aria-labelledby="risks"><h2 id="risks">Customer risks and failures</h2><ul>{risk_markup}</ul></section>

  <section aria-labelledby="journeys"><h2 id="journeys">Customer journeys</h2>{journey_cards or '<p class="muted">No journeys were requested.</p>'}</section>

  <p class="notice">Evidence source: {_esc(payload["evidence"]["source"])}. Validation level: {_esc(payload["evidence"]["validation"])}.</p>
</main>
</body>
</html>
"""


def write_html(
    path: str | Path,
    run: RunResult,
    gate: GateResult | None = None,
    *,
    include_trace: bool = False,
) -> Path:
    """Write a self-contained HTML report and return its path."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_html(run, gate, include_trace=include_trace), encoding="utf-8")
    return destination


def _journey_card(journey: JourneyResult, *, include_trace: bool) -> str:
    status = journey.status.value
    checks = []
    for evaluator in journey.evaluators:
        for check in evaluator.checks:
            evidence = "".join(f"<li>{_esc(item)}</li>" for item in check.evidence)
            checks.append(
                f"<div class=\"check\"><h4>{_esc(check.check_id)} "
                f"<span class=\"status status-{check.status.value}\">{_esc(check.status.value.upper())}</span></h4>"
                f"<p>{_esc(check.summary)}</p><p><span class=\"label\">Customer effect:</span> {_esc(check.customer_effect)}</p>"
                f"{('<p><span class=\"label\">Error:</span> ' + _esc(check.error) + '</p>') if check.error else ''}"
                f"{('<p class=\"label\">Evidence</p><ul>' + evidence + '</ul>') if evidence else ''}</div>"
            )
    if journey.error:
        checks.insert(0, f"<p><span class=\"label\">Execution or evaluation error:</span> {_esc(journey.error)}</p>")
    check_markup = "".join(checks) or '<p class="muted">No evaluator checks were recorded.</p>'
    trace_markup = ""
    if include_trace and journey.trace is not None:
        trace_markup = f"<details><summary>Trace detail</summary><pre>{_esc(json.dumps(journey.trace.to_dict(), indent=2, sort_keys=True, default=str))}</pre></details>"
    return f"""<article>
  <header><h3>{_esc(journey.scenario.title)}</h3><span class="status status-{status}">{_esc(status.upper())}</span></header>
  <p class="meta">{_esc(journey.scenario.category)} · case <code>{_esc(journey.scenario.id)}</code> · completed: {_esc(str(journey.completed))}</p>
  {check_markup}{trace_markup}
</article>"""


def _risk_items(run: RunResult) -> list[str]:
    risks: list[str] = []
    for journey in run.journeys:
        if journey.error:
            risks.append(f"{journey.scenario.title}: the journey could not be completed ({journey.error}).")
        for evaluator in journey.evaluators:
            for check in evaluator.checks:
                if check.status in (ResultStatus.UNSAFE, ResultStatus.FAIL, ResultStatus.ERROR):
                    risks.append(f"{journey.scenario.title} · {check.check_id}: {check.customer_effect or check.summary}")
    return risks


def _metric(label: str, value: str, detail: str) -> str:
    return f'<div class="metric"><strong>{_esc(value)}</strong><span>{_esc(label)}</span><br><span>{_esc(detail)}</span></div>'


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
