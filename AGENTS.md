# Support Evals operating contract

## Product boundary

Build a reusable, product-neutral evaluation framework for customer-support AI. It evaluates a customer case from first contact through resolution, safe refusal, or handoff.

This repository does not contain a customer-facing support bot and does not claim production validation.

## Language

Use customer-support language in reports and documentation. Explain the customer effect of every failure. Define technical terms when they cannot be avoided.

## Evidence

- Local versioned cases, JSON results, and HTML reports are the source of truth.
- Langfuse is an optional comparison and review destination.
- Never hide requested cases, incomplete runs, execution errors, abstentions, or unsafe outcomes.
- Keep exact checks separate from AI and human judgment.
- Do not claim that synthetic or local evidence predicts production customer outcomes.

## Architecture

- Keep the core runner product-neutral.
- Connect products through small adapters.
- Keep support concerns in optional evaluation packs.
- Use Python 3.11+ and the standard library for the initial framework.
- Do not add dependencies or edit dependency files without Adi's approval.
- Voice is a first-class optional pack; do not rebuild telephony infrastructure.

## UI

Generated HTML reports use Kora Tier 3 because this is a public editorial QA report, not a Kora product interface.

## Scope control

Do not copy whole implementations from sibling repositories. Extract contracts and behaviours, preserve provenance in documentation, and write clean product-neutral code.
