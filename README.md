# Support Evals

A helpful reply does not tell me whether support actually helped. I built Support Evals to check the recorded investigation, guidance, actions and handoff—not only the last answer.

It has been tested with fictional cases, saved records and local component connections. It has not been validated on production customer traffic. Reviewing two Voice navigation scenarios through accessibility and vision, plus one continuing Copilot session, found a gap that successful navigation checks missed: Voice's main message could retain the opening instruction after guidance advanced. The response is repaired. The recorded-review tool retains those older failures and checks three new controlled outcome variants. Human judgment of support usefulness remains separate from those checks.

Most AI evaluations grade the reply. Customer support can fail before and
after that reply: the system can misunderstand the customer, guess a cause too
early, promise an action that never happened, or hand the case to a person with
no useful context.

Support Evals reviews the complete customer journey—from the first contact to
a verified resolution, a safe refusal, or a useful handoff.

## What it reviews

- **Understanding:** Did the system understand the customer's actual need and
  preserve important details such as dates, amounts, corrections, and “not”?
- **Investigation:** Did it gather enough evidence before naming a cause or
  choosing a fix?
- **Guidance and safety:** Was the answer supported, relevant, and free of
  unsafe promises or invented facts?
- **Action and outcome:** Did the promised action happen, and did the product
  reach the expected state?
- **Closure:** Was the case resolved, honestly blocked, or handed over with
  enough context for the next person to continue?

Voice support adds checks for hearing, response timing, interruptions, silence,
repeated customer information, and the final call outcome.

## The method

The framework uses **evidence-gated journey QA**:

> A support decision should not pass QA unless the journey contains the
> evidence needed to defend it.

For technical evidence timing, a fact counts only when a `system`
`observation`, `tool_result`, or `state_check` event recorded it before the
step. Customer and agent messages can explain a fact but cannot establish it
for this check. The adapter must preserve the event actor and kind from the
captured record.

Conclusion checks only test whether the agent recorded a required conclusion.
They do not establish that the conclusion caused or explains the outcome. This
framework relies on the adapter to preserve source labels and factual records;
it cannot independently verify their authenticity.

Each run follows the same shape:

```text
customer case
    ↓
reference adapter
    ↓
complete journey record
    ↓
support QA checks
    ↓
QA result + saved evidence
```

The checks can change by product. The support principles do not.

## Honest boundary

This repository has been tested with fictional cases, saved traces, controlled
product states, and local reference adapters. It has not been validated on
production customer traffic. A local Handoff-to-Evals check connects those components; it does not establish that the complete customer experience works.

It can show that the framework catches the support failures represented in its
cases. It cannot show that using the framework improves CSAT, resolution rate,
customer effort, or safety in a support operation.

Real use would provide the missing feedback loop: human QA disagreement,
escalations, customer complaints, unexpected journeys, and business outcomes
would reveal where the cases and rules are wrong or incomplete.

## What the repaired checks catch

Suppose AI tells a customer to change a setting before checking the app. Later, it checks the app and repeats the instruction with proper evidence. The later correct step must not erase the earlier unsupported one. The checker reviews each occurrence separately.

For an urgent handoff, it also checks that the application recorded who released the case, why it could not wait and the intended recipient. An AI sentence claiming it sent a case is not a receipt from the receiving system. These checks depend on trustworthy application records.

## What happened when applied to the prototypes

A retrospective review found a concrete Voice Support defect: the main response kept the first instruction after the guidance had advanced. The on-screen caption was correct, which hid the inconsistency from the test page. The shared response was repaired and checked with three controlled customer outcomes: yes, no and unsure.

The review keeps the earlier native runs marked as failures for that message check. It also retains provider failures rather than replacing them with the successful retry. The new controlled replays check the repair; they are not new real-model, microphone or native-window trials.

The saved Copilot conversation exposes the order of questions, source reads and advice. The reviewer deliberately abstains on whether that advice was useful and whether a receiving person acted. Those need a human judgment or an actual receipt. Recording a proposed escalation is not proof that it happened.

Run the recorded-development reviewer with:

```sh
python3 -m support_evals.recorded_journeys path/to/captured-run.json \
  --output /tmp/recorded-review.json
```

It retains source fingerprints and event references. Repeated attempts are not independent scenarios, and these selected records do not give a customer-success rate. The maintained suite contains 78 checks, including tests that old failures cannot be hidden by a later pass.

## A normal technical-support example

A customer's home-security camera went offline after the Wi-Fi password
changed. They already restarted it.

A weak system repeats generic restart instructions. A good system uses the
existing case history, investigates the network change, guides the customer
through the right reconnect steps, confirms whether the camera came back
online, and creates a complete handoff if recovery fails.

Support Evals checks that journey, not only whether the final reply sounds
helpful.

## Run the fictional reference shop

Requirements: Python 3.11 or newer. The framework uses only the Python standard
library.

```bash
python3 -m support_evals list
python3 -m support_evals plan --adapter reference-shop
python3 -m support_evals run --adapter reference-shop \
  --output /tmp/support-evals-shop.json \
  --html /tmp/support-evals-shop.html
```

The reference shop contains fictional technical support, account access,
delivery, billing, and engineering-handoff cases. It does not contact customers
or change a live system.

To see a serious support fault block the result:

```bash
python3 -m support_evals run --adapter reference-shop \
  --mutation unsafe-promise
```

## Run a captured voice journey

The voice pack reads a saved, provider-neutral call trace. It does not place a
phone call or require a voice vendor.

```bash
python3 -m support_evals run --adapter reference-voice --case passing \
  --output /tmp/support-evals-voice.json \
  --html /tmp/support-evals-voice.html
```

Try a known voice failure:

```bash
python3 -m support_evals run --adapter reference-voice --case broken-action
```

The included broken cases cover lost meaning, slow responses, speaking over the
customer, long silence and repetition, the wrong support action, and the wrong
final outcome.

## Connect another support product

A product connects through a small adapter. The adapter has two jobs:

1. List the customer cases that should run.
2. Return the observed conversation, actions, handoff, and final product state
   as a common `Trace`.

The shared runner then applies the evaluation profile that fits the product.
For a real integration, start with saved transcripts, a product sandbox, or a
local test environment. Customer access is not required to connect the
framework.

The main contracts are in [`support_evals/contracts.py`](support_evals/contracts.py).
The reusable support checks are in [`support_evals/packs/`](support_evals/packs/).
The fictional shop adapter is in
[`support_evals/reference/shop.py`](support_evals/reference/shop.py).

## Results and review

Every run can produce two local files:

- **JSON** is the exact evidence record for automation and later review.
- **HTML** explains the decision and customer effect in plain language.

Errors, incomplete cases, abstentions, unsafe outcomes, and failed checks stay
visible. A release gate cannot turn them into a silent pass.

Langfuse is optional. The included exporter can prepare a privacy-safe review
copy, but Langfuse does not control the local result:

```bash
python3 -m support_evals run --adapter reference-shop \
  --langfuse-dry-run \
  --langfuse-output /tmp/support-evals-langfuse.json
```

## Read the argument, not the test report

[`QA in Customer Support, 2026`](examples/output/qa-in-customer-support-2026.html)
explains the support ideas behind this project: why grading only the answer is
too weak, why synthetic customers can flatter a system, why early diagnosis is
still bad support, and why the QA reviewer also needs QA.

The detailed cross-project evidence remains available as an appendix:

- [`support-portfolio-report-2026-08-29.html`](examples/output/support-portfolio-report-2026-08-29.html)
- [`support-portfolio-run-2026-08-29.json`](examples/output/support-portfolio-run-2026-08-29.json)

## Repository map

```text
support_evals/          core contracts, runner, reports, and integrations
support_evals/packs/    reusable support QA checks
support_evals/voice/    optional captured-voice checks
examples/               fictional chat and voice journeys
scripts/                article and portfolio report renderers
tests/                  framework and deliberate-failure tests
SPEC.md                 product boundary and acceptance rules
```
