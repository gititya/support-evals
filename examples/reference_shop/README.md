# Reference shop

This is a safe local B2C support operation for trying Support Evals. It uses
synthetic customers and records structured support facts, tool calls, handoffs
and final account state. It includes a camera connection problem, account
access, a missing delivery, a post-cancellation charge and an engineering
handoff.

Run it from the repository root with:

```python
from support_evals import run_suite
from support_evals.packs import standard_profile, support_evaluators
from support_evals.reference import ReferenceShopAdapter

adapter = ReferenceShopAdapter()
result = run_suite(
    adapter,
    adapter.list_scenarios(),
    profile=standard_profile(),
    evaluators=support_evaluators(),
)
print(result.counts.to_dict())
```

The expected result is five requested and completed journeys, all passing.
The evidence is synthetic and local. It does not predict production customer
outcomes.
