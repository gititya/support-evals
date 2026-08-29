# Support Evals 0.1 specification

## Product promise

A support team can describe customer journeys, connect a support agent, run those journeys, and receive an honest QA report covering resolution, safe refusal, or handoff.

## Claim boundary

Version 0.1 is production-shaped and locally tested. It is not production-validated. Every report states its evidence source.

## Users

- Support leaders read the HTML report.
- Support QA authors cases and release rules.
- Product and engineering teams connect the support system and investigate traces.

## Complete journey

A journey begins with a customer goal and initial product state. It ends only when the goal is resolved, an allowed refusal is explained, or a complete human handoff is produced.

## Required framework parts

1. Versioned scenario and result contracts.
2. A small adapter boundary for the system being tested.
3. Repeatable runs with full traces.
4. Exact support checks and optional judgment checks.
5. Fixed release gates set before the run.
6. Local JSON and HTML results.
7. Optional Langfuse export that cannot alter the local verdict.
8. A fictional B2C reference operation.
9. A first-class optional voice pack.

## Initial support packs

- Answer quality and policy grounding.
- Evidence-timed technical investigation.
- Intent, risk, routing, and handoff.
- Tool use and final-state verification.
- Unsafe and adversarial requests.
- Voice meaning, timing, interruption, and outcome.

## Reference journeys

- Home-security camera offline after a Wi-Fi password change.
- Duplicate charge after subscription cancellation.
- Account access with insufficient identity evidence.
- Delivery marked complete but not received.
- Failed technical recovery requiring an engineering handoff.
- Voice caller corrects a date and interrupts an incorrect assumption.

## Acceptance matrix

| Requirement | Acceptance evidence |
|---|---|
| Another product can connect | A second fixture adapter runs without changing core code |
| A customer journey can run | Reference case produces a complete trace and final state |
| Serious harm blocks release | An unsafe promise or unverified action makes the profile fail |
| Broken evaluators are visible | Mutation fixtures cause their intended checks to fail |
| Results stay honest | Requested, completed, failed, errors, abstentions, and unsafe outcomes remain visible |
| Support leaders can read it | One self-contained HTML report explains customer effect in plain language |
| Builders can automate it | CLI exit status and JSON report work without the HTML view |
| Langfuse stays optional | Export failure cannot change or erase the local result |
| Voice is included | A voice journey records hearing, timing, interruption, support action, and outcome checks |
| No production overclaim | README and reports state the evidence source and validation level |

## Out of scope for 0.1

- A hosted dashboard.
- Telephony or media-stream infrastructure.
- Automatic production sampling.
- Replacement of human QA.
- Screen-aware guidance and complaint-theme mining.
- Claims about CSAT, resolution, or production safety.
