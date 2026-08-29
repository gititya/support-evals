import unittest

from support_evals.reference import BrokenReferenceAdapter, REFERENCE_SCENARIOS, ReferenceShopAdapter


class ReferenceShopTests(unittest.TestCase):
    def test_reference_operation_covers_support_and_technical_cases(self):
        adapter = ReferenceShopAdapter()
        self.assertEqual(len(REFERENCE_SCENARIOS), 5)
        categories = {scenario.category for scenario in adapter.list_scenarios()}
        self.assertTrue({"technical-support", "account-support", "delivery-support", "billing-support"} <= categories)
        self.assertTrue(any("camera" in scenario.title.lower() for scenario in REFERENCE_SCENARIOS))
        self.assertTrue(any("handoff" in tag for scenario in REFERENCE_SCENARIOS for tag in scenario.tags))

    def test_broken_adapter_is_named_and_deterministic(self):
        adapter = BrokenReferenceAdapter()
        trace_one = adapter.run(REFERENCE_SCENARIOS[3])
        trace_two = adapter.run(REFERENCE_SCENARIOS[3])
        self.assertEqual(trace_one, trace_two)
        self.assertEqual(adapter.name, "reference-shop-broken")

    def test_unknown_suite_is_empty(self):
        self.assertEqual(ReferenceShopAdapter().list_scenarios("unknown"), ())


if __name__ == "__main__":
    unittest.main()
