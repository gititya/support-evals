import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lessons" / "what-i-learned-building-support-products.html"
METHOD = ROOT / "lessons" / "what-i-learned-building-support-products-methodology.md"


def visible_text(rendered: str) -> str:
    rendered = re.sub(r"<style>[\s\S]*?</style>", " ", rendered)
    rendered = re.sub(r"<script>[\s\S]*?</script>", " ", rendered)
    return re.sub(r"<[^>]+>", " ", rendered)


class LearningLessonTests(unittest.TestCase):
    def setUp(self):
        self.rendered = LESSON.read_text(encoding="utf-8")

    def test_teaches_decisions_and_claim_boundary(self):
        self.assertIn("What I learned from building support products", self.rendered)
        self.assertIn("Only say or do what the available evidence", self.rendered)
        self.assertIn("Build, adapt, or kill", self.rendered)
        self.assertIn("Verified now", self.rendered)
        self.assertIn("Reasonable inference", self.rendered)
        self.assertIn("Not yet known", self.rendered)

    def test_distinguishes_source_methods_from_shared_harness(self):
        self.assertIn("The source methods and the new harness are not the same thing", self.rendered)
        self.assertIn("fictional reference shop", self.rendered)
        self.assertIn("provider-neutral captured-voice", self.rendered)
        self.assertIn("Screen-aware guidance and complaint-theme mining are explicitly outside", self.rendered)

    def test_avoids_decorative_score_totals(self):
        visible = visible_text(self.rendered)
        self.assertIsNone(re.search(r"\b\d+\s*/\s*\d+\b", visible))
        self.assertNotIn("repo grade", visible.lower())
        self.assertNotIn("score badge", visible.lower())

    def test_interactions_have_accessible_feedback(self):
        self.assertIn('class="skip-link"', self.rendered)
        self.assertGreaterEqual(self.rendered.count('aria-live="polite"'), 4)
        self.assertIn("timelineButtons.forEach", self.rendered)
        self.assertIn("journeyButtons.forEach", self.rendered)
        self.assertIn("decisionButtons.forEach", self.rendered)
        self.assertIn("document.querySelectorAll('.scenario')", self.rendered)

    def test_is_self_contained_and_network_silent(self):
        self.assertNotIn("<script src=", self.rendered)
        self.assertNotIn("<link rel=\"stylesheet\"", self.rendered)
        self.assertNotIn("fetch(", self.rendered)
        self.assertNotIn("XMLHttpRequest", self.rendered)
        self.assertNotIn("WebSocket", self.rendered)

    def test_methodology_records_continuation_contract(self):
        methodology = METHOD.read_text(encoding="utf-8")
        self.assertIn("## Evidence method", methodology)
        self.assertIn("## Source boundaries", methodology)
        self.assertIn("## Synthesis rules", methodology)
        self.assertIn("## Claim language", methodology)
        self.assertIn("## How Adi's feedback shaped the artifact", methodology)
        self.assertIn("## Continuation rules for another agent", methodology)


if __name__ == "__main__":
    unittest.main()
