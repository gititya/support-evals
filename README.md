A support reply can sound helpful while the customer is still stuck. I wanted to check the work behind the reply: what the system understood, what it did, and whether the customer could actually move forward.

## What I built

A way to review recorded support journeys against clear expectations:

1. **Understanding:** did it use what the customer and product had already told it?

2. **Investigation:** did it ask something useful, or repeat a question already answered?

3. **Guidance:** did the instruction match the step the customer was on?

4. **Outcome:** was the fix confirmed, or merely suggested?

5. **Handoff:** was the case received, with enough context for the next person?

Some checks compare the recorded actions and outcomes with explicit rules. Questions such as whether advice was useful still need human review.

## What it found

This evaluation system was used to review selected journeys from [Voice Support](https://github.com/gititya/voice-support-case-study). In one review, the outline moved to the next control, but the main message kept repeating the opening instruction. Looking only at whether the correct screen appeared had missed this. The customer was getting two different instructions.

That problem was repaired and checked again. The earlier failed attempts remain in the record; a successful retry does not erase them.

The same evaluation system also reviewed selected journeys from [Copilot Lab](https://github.com/gititya/support-copilot-lab) and [Handoff Gate](https://github.com/gititya/handoff-gate). The checks distinguish a proposed fix from confirmed recovery, and a prepared escalation from acknowledgement by the receiving system.

## What I took away

**Support QA needs to follow the investigation and the customer's progress, not just grade the final answer.**

For an AI system, that means asking what evidence was available when it made a decision. A correct answer reached through unsupported assumptions is different from one grounded in the customer's case.

## Where this stops

This is an experiment using authored scenarios and selected prototype journeys. It is not a score for a real support operation. It does not prove that customers resolve problems faster, or that reps find every suggestion useful. It also relies on the records supplied to it; it cannot independently establish that every recorded claim is true.

The value so far is concrete: it exposed a customer-facing failure that a narrower check had missed.
