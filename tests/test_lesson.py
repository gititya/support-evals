import re
import unittest
from pathlib import Path


LESSON = Path(__file__).resolve().parents[1] / "lessons" / "how-i-run-support-evals.html"


class LessonTests(unittest.TestCase):
    def test_lesson_teaches_framework_and_claim_boundary(self):
        rendered = LESSON.read_text(encoding="utf-8")
        self.assertIn("Evidence-gated journey QA", rendered)
        self.assertIn("The customer journey, not the last reply", rendered)
        self.assertIn("The portfolio and the reusable framework are not the same thing", rendered)
        self.assertIn("It is not a production-proven QA system", rendered)
        self.assertIn("Retrieval practice", rendered)

    def test_lesson_keeps_score_counts_out_of_visible_prose(self):
        rendered = LESSON.read_text(encoding="utf-8")
        visible = re.sub(r"<style>[\s\S]*?</style>", " ", rendered)
        visible = re.sub(r"<script>[\s\S]*?</script>", " ", visible)
        visible = re.sub(r"<[^>]+>", " ", visible)
        self.assertIsNone(re.search(r"\b\d+\s*/\s*\d+\b", visible))
        self.assertIsNone(re.search(r"\b\d+(?:\.\d+)?%", visible))

    def test_interactive_controls_have_feedback_targets(self):
        rendered = LESSON.read_text(encoding="utf-8")
        self.assertIn('aria-live="polite"', rendered)
        self.assertIn("journeyButtons.forEach", rendered)
        self.assertIn("document.querySelectorAll('.quiz')", rendered)


if __name__ == "__main__":
    unittest.main()
