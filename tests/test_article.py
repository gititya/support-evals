import tempfile
import unittest
import re
from pathlib import Path

from support_evals.article import render_article_html, write_article_html


class ArticleTests(unittest.TestCase):
    def test_article_is_editorial_and_escapes_dynamic_metadata(self):
        payload = {"generated_at": "29 <August>"}
        rendered = render_article_html(payload)
        self.assertIn("QA in Customer Support, 2026", rendered)
        self.assertIn("taking customer calls as a support rep in 2011", rendered)
        self.assertIn("29 &lt;August&gt;", rendered)
        self.assertNotIn('role="tab"', rendered)

    def test_article_keeps_scores_in_the_appendix(self):
        rendered = render_article_html({})
        self.assertIsNone(re.search(r"\b\d+\s*/\s*\d+\b", rendered))
        self.assertNotIn('class="stat', rendered)
        self.assertIn("Practice customers can make a weak system look good", rendered)
        self.assertIn("Support QA in 2026 should move from policing words to proving decisions", rendered)

    def test_article_is_self_contained_and_writable(self):
        payload = {"products": [], "framework_checks": []}
        rendered = render_article_html(payload)
        self.assertIn("<style>", rendered)
        self.assertNotIn("<script", rendered)
        with tempfile.TemporaryDirectory() as directory:
            path = write_article_html(Path(directory) / "article.html", payload)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
