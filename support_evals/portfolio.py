"""Plain-language portfolio report for support evaluation evidence."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping


_STATUS_LABELS = {
    "strong": "Works well locally",
    "mixed": "Works, but has problems",
    "blocked": "Could not be certified",
    "partial": "Only part was tested",
    "infrastructure": "Supplies test cases",
}


def render_portfolio_html(payload: Mapping[str, Any]) -> str:
    """Render one self-contained report for support leaders."""

    products = list(payload.get("products", []))
    findings = list(payload.get("findings", []))
    limits = list(payload.get("limits", []))
    framework = list(payload.get("framework_checks", []))
    simple_summary = list(payload.get("simple_summary", []))
    next_steps = list(payload.get("next_steps", []))
    statuses: dict[str, int] = {}
    for product in products:
        status = str(product.get("status", "partial"))
        statuses[status] = statuses.get(status, 0) + 1

    status_metrics = "".join(
        _metric(_STATUS_LABELS.get(key, key.replace("_", " ").title()), str(value))
        for key, value in statuses.items()
    )
    product_cards = "".join(_product_card(product) for product in products)
    finding_items = "".join(f"<li>{_esc(item)}</li>" for item in findings)
    limit_items = "".join(f"<li>{_esc(item)}</li>" for item in limits)
    framework_rows = "".join(_framework_row(row) for row in framework)
    simple_cards = "".join(
        f'<article class="simple-card"><h3>{_esc(row.get("title", ""))}</h3>'
        f'<p>{_esc(row.get("text", ""))}</p></article>'
        for row in simple_summary
    )
    next_step_items = "".join(f"<li>{_esc(item)}</li>" for item in next_steps)
    source_check = payload.get("source_check", {})

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(payload.get('title', 'Support evaluation portfolio'))}</title>
  <style>
    :root {{ color-scheme:dark; --bg:#171411; --surface:#211d19; --surface2:#2b2520; --text:#f3eee7; --muted:#c6bbae; --line:#554a40; --accent:#f0cc7a; --good:#8ed3a9; --bad:#ff9c8a; --info:#9ec7df; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ max-width:1180px; margin:0 auto; padding:32px 20px 72px; }}
    h1,h2,h3 {{ line-height:1.18; }} h1 {{ margin:.25rem 0 .75rem; font-size:clamp(2rem,5vw,3.8rem); max-width:18ch; }} h2 {{ margin-top:0; }}
    .eyebrow,.status,.tab {{ font:700 .78rem/1.2 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.12em; text-transform:uppercase; }}
    .eyebrow,.muted,.note {{ color:var(--muted); }} .lede {{ color:var(--muted); max-width:78ch; font-size:1.08rem; }}
    .verdict {{ display:inline-block; margin:14px 0; padding:10px 14px; border:1px solid var(--accent); border-radius:8px; color:var(--accent); font-weight:750; }}
    .tabs {{ display:flex; flex-wrap:wrap; gap:8px; margin:30px 0 20px; border-bottom:1px solid var(--line); padding-bottom:12px; }}
    .tab {{ appearance:none; border:1px solid var(--line); border-radius:8px; padding:10px 12px; color:var(--muted); background:var(--surface); cursor:pointer; }}
    .tab[aria-selected="true"] {{ color:var(--bg); border-color:var(--accent); background:var(--accent); }}
    .panel[hidden] {{ display:none; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin:20px 0 28px; }}
    .metric,.card,.callout,.simple-card {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; }}
    .metric {{ padding:14px; }} .metric strong {{ display:block; font-size:1.55rem; }} .metric span {{ color:var(--muted); }}
    .card {{ padding:18px; margin:12px 0; }} .card header {{ display:flex; gap:12px; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; }}
    .card h3 {{ margin:0; }} .card h4 {{ margin:1.2rem 0 .3rem; }} .card p {{ max-width:90ch; }}
    .status {{ white-space:nowrap; }} .status-strong {{ color:var(--good); }} .status-mixed,.status-partial {{ color:var(--accent); }} .status-blocked {{ color:var(--bad); }} .status-infrastructure {{ color:var(--info); }}
    .evidence {{ width:100%; border-collapse:collapse; margin-top:12px; }} .evidence th,.evidence td {{ padding:10px 8px; text-align:left; vertical-align:top; border-top:1px solid var(--line); }} .evidence th {{ color:var(--muted); font-size:.86rem; }}
    .callout {{ padding:18px; margin:16px 0; border-left:4px solid var(--accent); }}
    .short-answer {{ font-size:1.18rem; max-width:72ch; }}
    .simple-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; margin:18px 0 30px; }}
    .simple-card {{ padding:20px; }} .simple-card h3 {{ margin:0 0 8px; font-size:1.05rem; }} .simple-card p {{ margin:0; color:var(--muted); }}
    ul {{ padding-left:1.25rem; }} li {{ margin:.4rem 0; }} code {{ color:var(--accent); }}
    a {{ color:var(--accent); }} :focus-visible {{ outline:3px solid var(--accent); outline-offset:3px; }}
    @media (max-width:650px) {{ .evidence,.evidence tbody,.evidence tr,.evidence td {{ display:block; }} .evidence thead {{ display:none; }} .evidence td {{ border-top:0; padding:3px 0; }} .evidence tr {{ border-top:1px solid var(--line); padding:10px 0; }} }}
  </style>
</head>
<body>
<main>
  <p class="eyebrow">Support Evals · cross-product run</p>
  <h1>{_esc(payload.get('title', 'Support evaluation portfolio'))}</h1>
  <p class="lede">{_esc(payload.get('plain_summary', ''))}</p>
  <p><span class="verdict">{_esc(payload.get('verdict', 'LOCAL EVIDENCE ONLY'))}</span></p>
  <p class="note">Run date: {_esc(payload.get('generated_at', ''))} · Evidence level: {_esc(payload.get('evidence_level', 'local and synthetic'))}</p>

  <nav class="tabs" aria-label="Report sections">
    <button class="tab" role="tab" aria-selected="true" aria-controls="summary" id="tab-summary">The answer</button>
    <button class="tab" role="tab" aria-selected="false" aria-controls="products" id="tab-products">Full evidence · optional</button>
    <button class="tab" role="tab" aria-selected="false" aria-controls="framework" id="tab-framework">How it works</button>
    <button class="tab" role="tab" aria-selected="false" aria-controls="limits" id="tab-limits">What is missing</button>
  </nav>

  <section class="panel" role="tabpanel" id="summary" aria-labelledby="tab-summary">
    <h2>The short answer</h2>
    <div class="callout short-answer"><strong>{_esc(payload.get('simple_verdict', 'You have built a useful local support QA test lab.'))}</strong><p>{_esc(payload.get('simple_verdict_detail', 'It has not yet been proven with real customers.'))}</p></div>
    <h2>What I found</h2>
    <div class="simple-grid">{simple_cards}</div>
    <h2>What I would do next</h2>
    <ol>{next_step_items}</ol>
    <details><summary>Show the run size and detailed findings</summary>
      <div class="grid">
        {_metric('Support areas reviewed', str(len(products)))}
        {_metric('Fresh automated checks', str(payload.get('fresh_automated_tests', '—')))}
        {status_metrics}
      </div>
      <p class="muted">These are different kinds of tests, so they do not form one pass rate.</p>
      <ul>{finding_items}</ul>
    </details>
  </section>

  <section class="panel" role="tabpanel" id="products" aria-labelledby="tab-products" hidden>
    <h2>The detailed evidence</h2>
    <p class="muted">You can skip this tab on the first read. It keeps the exact results for anyone who wants to check how each conclusion was reached.</p>
    {product_cards}
  </section>

  <section class="panel" role="tabpanel" id="framework" aria-labelledby="tab-framework" hidden>
    <h2>How the reusable framework behaved</h2>
    <p>The framework reads a saved customer journey, runs the support checks chosen for that product, keeps every failure in the count, and writes local JSON plus this HTML view.</p>
    <table class="evidence"><thead><tr><th>Test</th><th>Result</th><th>Why a support leader should care</th></tr></thead><tbody>{framework_rows}</tbody></table>
    <div class="callout"><strong>How this gets reused:</strong> each support product supplies a small translator that turns its saved conversation, actions, handoff, and final state into the common journey format. The shared checks then run without copying the product into this repo.</div>
  </section>

  <section class="panel" role="tabpanel" id="limits" aria-labelledby="tab-limits" hidden>
    <h2>What this run cannot claim</h2>
    <ul>{limit_items}</ul>
    <h3>Source-repository check</h3>
    <p>{_esc(source_check.get('summary', 'Not recorded.'))}</p>
    <p class="note">{_esc(source_check.get('detail', ''))}</p>
  </section>
</main>
<script>
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const panels = [...document.querySelectorAll('[role="tabpanel"]')];
  tabs.forEach(tab => tab.addEventListener('click', () => {{
    tabs.forEach(item => item.setAttribute('aria-selected', String(item === tab)));
    panels.forEach(panel => panel.hidden = panel.id !== tab.getAttribute('aria-controls'));
    tab.focus();
  }}));
</script>
</body>
</html>
"""


def write_portfolio_html(path: str | Path, payload: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_portfolio_html(payload), encoding="utf-8")
    return destination


def load_portfolio_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _product_card(product: Mapping[str, Any]) -> str:
    status = str(product.get("status", "partial"))
    evidence_rows = "".join(
        "<tr>"
        f"<td>{_esc(row.get('measure', ''))}</td>"
        f"<td><strong>{_esc(row.get('result', ''))}</strong></td>"
        f"<td>{_esc(row.get('note', ''))}</td>"
        "</tr>"
        for row in product.get("evidence", [])
    )
    issues = "".join(f"<li>{_esc(item)}</li>" for item in product.get("issues", []))
    not_run = "".join(f"<li>{_esc(item)}</li>" for item in product.get("not_run", []))
    issues_block = f"  <h4>Problems found</h4><ul>{issues}</ul>\n" if issues else ""
    not_run_block = f"  <h4>Not run now</h4><ul>{not_run}</ul>\n" if not_run else ""
    return f"""<article class="card">
  <header><div><p class="eyebrow">{_esc(product.get('eval_type', 'Support evaluation'))}</p><h3>{_esc(product.get('name', 'Unnamed product'))}</h3></div><span class="status status-{_esc(status)}">{_esc(_STATUS_LABELS.get(status, status))}</span></header>
  <p><strong>What it checks:</strong> {_esc(product.get('what_it_checks', ''))}</p>
  <p><strong>Customer meaning:</strong> {_esc(product.get('customer_meaning', ''))}</p>
  <table class="evidence"><thead><tr><th>Fresh evidence</th><th>Result</th><th>What to know</th></tr></thead><tbody>{evidence_rows}</tbody></table>
{issues_block}{not_run_block}  <p class="note">Claim limit: {_esc(product.get('boundary', 'Local evidence only.'))}</p>
</article>"""


def _framework_row(row: Mapping[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_esc(row.get('test', ''))}</td>"
        f"<td><strong>{_esc(row.get('result', ''))}</strong></td>"
        f"<td>{_esc(row.get('meaning', ''))}</td>"
        "</tr>"
    )


def _metric(label: str, value: str) -> str:
    return f'<div class="metric"><strong>{_esc(value)}</strong><span>{_esc(label)}</span></div>'


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
