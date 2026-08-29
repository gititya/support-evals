# Voice pack integration contract

The voice pack evaluates a **captured voice journey**. It is not a live-call
engine and does not provide telephony, media streaming, audio capture,
speech-to-text, or a vendor SDK.

## Import boundary

An EVA, tau-bench, or in-house adapter may export a call trace, but it must
normalize it into `support_evals.voice.capture_to_trace` first. The normalized
capture has this shape:

```json
{
  "events": [
    {
      "sequence": 1,
      "actor": "customer",
      "kind": "speech_end",
      "content": "My camera failed on Friday, not Thursday.",
      "data": {
        "end_ms": 1000,
        "entities": {"incident_date": "Friday"},
        "negations": ["not Thursday"]
      }
    },
    {
      "sequence": 2,
      "actor": "agent",
      "kind": "speech_start",
      "content": "Thanks, I have Friday.",
      "data": {"start_ms": 1600, "latency_ms": 600, "entities": {"incident_date": "Friday"}}
    }
  ],
  "final_state": {"camera_status": "online"},
  "metadata": {"customer_repetitions": 0}
}
```

Adapters should preserve the caller's critical entities and negations in event
metadata when a provider supplies structured transcript facts. Timing should
use milliseconds. An interruption event should include `yielded: true` when
the agent stopped or yielded the turn. Tool/action events should include an
action `name` and `success`; handoff events should include `summary` and
`reason`.

The pack checks meaning preservation, response latency, interruption yield,
silence, repeated customer information, expected support action, final state,
and safe handoff. Missing capture signals are reported as abstentions rather
than silently counted as passes. Local JSON remains the verdict; a future
observability export is only a viewing destination.
