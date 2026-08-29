# Reference voice traces

These captures describe a normal B2C technical-support journey: a caller's
home-security camera went offline after a Wi-Fi password change. The caller
corrects the date and account number, then interrupts an incorrect assumption
that the camera is defective.

Each JSON file contains a scenario expectation and a captured trace. The
passing capture should pass all voice checks. The broken captures each contain
one intentional defect: a lost fact, slow response, failure to yield, excess
silence, repeated information, missing recovery action, wrong final state, or
an incomplete handoff.

Run them with:

```python
from pathlib import Path
import json
from support_evals import Scenario
from support_evals.voice import VoiceEvaluator, capture_to_trace

case = json.loads(Path("examples/reference_voice/passing.json").read_text())
result = VoiceEvaluator().evaluate(Scenario.from_dict(case["scenario"]), capture_to_trace(case["trace"]))
```

These are captured-trace fixtures, not evidence that any live call or
production support system is safe.
