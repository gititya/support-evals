# Methodology and provenance handoff

## Artifact

- Lesson: `lessons/what-i-learned-building-support-products.html`
- Title: **What I Learned from Building Support Products**
- Audience: Adi, an experienced B2C customer-support leader who does not need an engineering-first explanation.
- Purpose: teach the judgment changes and reusable decision methods produced by the support-product work.
- Design tier: Kora Tier 3. Reason: this is a standalone editorial teaching artifact, not a Kora product interface.

## Core editorial decision

The lesson is not a portfolio inventory. It starts with the repeated support failure: a system can look complete before the customer is safe. It then shows how one contradicted assumption led to the next method.

The main synthesis is:

> Only say or do what the available evidence at that point in the customer journey supports.

This is called **evidence-gated support decisions** in the lesson. It is a synthesis across the work, not a claim that Adi invented a new evaluation field.

## Evidence method

1. Read the current learning artifacts first to establish Adi's level, language, and known corrections.
2. Treat prior lessons, Atlas pages, reports, and summaries as leads, not proof.
3. Check important claims against the current source repo's `AGENTS.md`, `SKILL.md`, `BUILDS.md`, README, specs, saved evidence, and implementation or tests where needed.
4. Record the private evidence worksheet by support problem, not repo: hypothesis, build, observed run, contradiction, customer effect, reusable rule, decision, source, and claim limit.
5. Synthesize only repeated judgment changes. Do not import every product or test into the visible lesson.
6. Keep decisive numbers only when they change a build decision. Interpret the number in the same sentence.
7. Separate what is verified now, inferred, and not yet known inside the lesson.

## Source boundaries

### Current reusable framework

The current `support-evals` repo directly runs:

- a fictional reference-shop adapter across complete chat journeys;
- a provider-neutral captured-voice adapter;
- reusable exact packs for answer evidence, technical investigation timing, intent/risk/routing/handoff, unsafe behavior, action verification, and final state;
- a captured-voice pack for meaning, response timing, interruption, silence, repetition, support action, final state, and handoff;
- local JSON and HTML results, with optional Langfuse export that cannot change the local verdict.

Primary files:

- `AGENTS.md`
- `BUILDS.md`
- `README.md`
- `SPEC.md`
- `support_evals/contracts.py`
- `support_evals/runner.py`
- `support_evals/packs/`
- `support_evals/voice/`
- `tests/`
- `examples/output/support-portfolio-run-2026-08-29.json`

Do not imply that all source products now run through this harness. `SPEC.md` explicitly keeps screen-aware guidance and complaint-theme mining outside version 0.1.

### Original source methods

The portfolio evidence record surveys the source products, but each method still lives in its original repo unless an adapter exists in `support-evals`.

#### Early prediction and investigation

- `/Users/aditya/Documents/Projects/real-time_support/`
  - Load-bearing assumption: exact root cause can be predicted from the opening turns.
  - Contradiction: stronger synthetic calls reduced early exact-cause accuracy to 2% against a 60% build gate, while full-call accuracy reached 92%.
  - Decision: kill broad early root-cause prediction; keep the pre-build validation method.
  - Claim limit: synthetic transcripts, not real calls.
- `/Users/aditya/Documents/Projects/experiments/support-copilot-lab/`
  - Pivot: maintain facts, unknowns, candidate branches, ruled-out paths, next checks, and evidence-timed final cause.
  - Decision: build the investigation method; reject lucky early diagnosis.
  - Claim limit: controlled B2B fixtures and offline replay, not a live helpdesk.

#### Meaning and routing

- `/Users/aditya/Documents/Projects/meaning-preserving_transcript-processing/`
  - Problem: transcript cleanup can change dates, amounts, corrections, uncertainty, or negation.
  - Decision: preserve raw meaning; use a separate verifier; do not treat cleanup as harmless.
  - Claim limit: local text corpora and saved pipeline evidence, not production audio.
- `/Users/aditya/Documents/Projects/support/voice-support/benchmarks/stt/`
  - Contradiction: default normalization increased support-critical failure for both tested speech paths.
  - Decision: leave normalization off in the product path.
  - Claim limit: locked local corpus, not a broad accent, language, channel, or production study.
- `/Users/aditya/Documents/Projects/experiments/intent_classifier/`
  - Contradiction: strong synthetic validation did not transfer to ten naturally worded customer messages; tested models reached only 20–50% on that small natural set.
  - Decision: do not claim automatic natural-language routing; use uncertainty and a human route while collecting better cases.
  - Claim limit: ten natural messages reveal risk but cannot estimate production accuracy.

#### Review and handoff

- `/Users/aditya/Documents/Projects/experiments/eval-judges/`
  - Contradiction: more detailed rubrics made the small source-of-truth judge worse; current calibration still exposes misses.
  - Decision: adapt AI review as a bounded, calibrated second look. Preserve exact checks and human QA.
  - Claim limit: local model and a small calibration set; not a human-QA replacement.
- `/Users/aditya/Documents/Projects/support/handoff-engine/`
  - Method: mechanical contract gates hold incomplete or unsupported handoffs; models may write a candidate note but do not own the pass/block decision.
  - Decision: build handoff as an outcome, not a route event.
  - Claim limit: synthetic flows; Contract A is mainly completeness, while stronger grounding is in Contract B.

#### State, action, and proof integrity

- `/Users/aditya/Documents/Projects/support/support-state-core/`
  - Method: deterministic risk floor, raise-only risk, bounded diagnostics, fail-closed routing, corrections, and evidence handles.
  - Decision: keep risky support judgment deterministic where the rule can be explicit.
  - Claim limit: controlled adversarial scenarios; no production traffic.
- `/Users/aditya/Documents/Projects/screen-aware-support/`
  - Method: registered-app scope, render-only guidance, customer-only action, fresh observation, stale-result rejection, and no actuation.
  - Contradiction: finding a target did not prove the customer completed the step.
  - Decision: separate `target_found` from `goal_state_reached`.
  - Claim limit: controlled and supervised local app evidence; no general desktop agent or production customer screen use.
- `/Users/aditya/Documents/Projects/support/support-binder/`
  - Method: bind cross-product proof to exact component commits, tags, and artifacts.
  - Contradiction: healthy component tests did not make a stale cross-product seal current.
  - Decision: keep version/proof integrity and block combined claims on drift.
  - Claim limit: local sealed replay, not a live desk or production system.

#### Wider operational proof

- `/Users/aditya/Documents/Projects/signal/`
  - Method: group public CFPB complaints into reviewable product signals.
  - Decision: keep complaint themes as evidence for review, not ground truth about prevalence or causality.
  - Claim limit: public complaint data; the current provider-based golden evaluation was not rerun in the fresh portfolio run.
- `/Users/aditya/Documents/Projects/support/internal-desk/`
  - Method: use read-only records, evidence-led outcomes, explicit representative confirmation, and honest blocking.
  - Decision: build operational closure with an evidence ledger.
  - Claim limit: local synthetic Zammad records, no paid model run or production customer case.
- `/Users/aditya/Documents/Projects/support/muesli-support-integration/`
  - Method: app-owned capability profile, registered Accessibility targets, non-actuating guidance, and version-bound live evidence.
  - Decision: adapt screen support per product and installed version; do not claim generic desktop coverage.
  - Claim limit: supervised local Muesli 0.8.3 proof, no customer-content read or input action.

## Learning sources read first

- `lessons/how-i-run-support-evals.html`
- `/Users/aditya/Documents/obsidian/attic/QA in Customer Support 2026.md`
- `/Users/aditya/Documents/obsidian/attic/Lessons/Support-Eval-Atlas.html`
- `/Users/aditya/Documents/obsidian/attic/Lessons/Support-Eval-Atlas-Corrected.html`
- `/Users/aditya/Documents/obsidian/attic/Lessons/Realtime support experiment.md`
- `/Users/aditya/Documents/obsidian/attic/Lessons/Realtime support_updated.md`
- `/Users/aditya/Documents/obsidian/attic/Lessons/Support-Quality.md`
- `/Users/aditya/Documents/obsidian/attic/Lessons/screen-aware-guidance-orchestration/`
- `/Users/aditya/Documents/obsidian/attic/Lessons/voice-support-realtime-architecture/`

The old Atlas supplied useful vocabulary and source leads, but its inventory and metric-heavy form was not reused. The corrected Atlas helped expose source-data and proof-level distinctions. Neither page was treated as current proof without live-file checks.

## Synthesis rules

- Lead with what changed Adi's mind.
- Explain customer effect before mechanism.
- Organize by support failure and decision, not repository.
- Prefer “I used to think / I learned” only when the source evidence supports the change.
- Use a negative result as a product decision, not a failed project grade.
- Treat a handoff, safe refusal, or honest block as a valid outcome when resolution is not supported.
- Separate target location, requested action, performed action, and verified state.
- Separate a model's verdict from the calibrated verdict and from a human judgment.
- Keep test-data authorship, hidden truth, and grader independence visible when they change the conclusion.
- Never add test counts as decorative credibility. Use a number only when it changes what should be built.
- Never merge unit tests, model trials, saved journeys, local app acceptance, and production results into one score.

## Claim language

Use:

- **Verified now:** supported by a current local file, saved artifact, focused run, or current source-repo state.
- **Inferred:** a synthesis across several verified findings; not directly measured as one result.
- **Not yet known:** requires real customers, production systems, broader samples, or a new live run.
- **Local / synthetic / controlled / supervised:** name the actual evidence source.
- **Promising:** useful evidence exists, but a needed proof layer is absent.
- **Blocked:** a required proof or dependency is missing; do not convert it to failure or success.

Avoid:

- “production proven,” “battle tested,” or “improves CSAT”;
- “all support products run through Support Evals”;
- “the AI resolved the case” when only a reply or tool request exists;
- “the reviewer is accurate” without its human baseline and false-safe boundary;
- “screen-aware” as a synonym for unrestricted screenshots, clicking, or desktop control;
- “passed” without naming the evidence type and scope.

## How Adi's feedback shaped the artifact

- The opening states the repeated support problem instead of listing projects.
- The timeline shows belief changes and killed ideas rather than release chronology.
- The customer effect appears before technical terms.
- Numbers appear only for the realtime kill gate and the synthetic-to-natural routing contradiction because those numbers changed the decision.
- The source-repo versus shared-harness distinction has its own visual section.
- The verified / inferred / unknown boundary appears before the exercises, not in a footer.
- Build / adapt / kill turns findings into decisions.
- Retrieval scenarios require Adi to choose the next support move and give immediate feedback.
- The page avoids grades, score badges, pass-total cards, and a dense product matrix.
- The glossary uses support language and defines the few technical terms that affect judgment.

## Continuation rules for another agent

1. Re-read this file and the current `support-evals/AGENTS.md` before revising the lesson.
2. Recheck drift-prone repo states and saved outputs before changing a claim.
3. Preserve the explicit source-repo versus current-harness boundary.
4. Add a new product example only if it changes a judgment or decision; do not turn the lesson into an inventory.
5. Keep customer outcomes ahead of implementation detail.
6. Do not replace the interactive lesson with dashboards, grade cards, or a portfolio score.
7. Preserve Kora Tier 3 and the self-contained, dependency-free HTML boundary.
8. Run the lesson tests, full repo tests, static security checks, and browser checks at desktop and mobile widths after edits.

## Verification target

The finished lesson should prove only that:

- the artifact teaches the supported judgment changes in plain support language;
- its claim limits are visible;
- the source-method versus shared-harness distinction is accurate;
- the interactions work by keyboard and pointer;
- the page reflows at narrow widths;
- the file is self-contained and makes no network request;
- existing repository tests still pass.

It must not claim that the lesson, the source portfolio, or Support Evals has improved a real customer's outcome.
