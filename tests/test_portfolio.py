import tempfile
import unittest
from pathlib import Path

from support_evals.portfolio import render_portfolio_html, write_portfolio_html


class PortfolioReportTests(unittest.TestCase):
    def test_report_escapes_product_fields_and_keeps_denominators(self):
        payload = {
            "title": "Support <portfolio>",
            "plain_summary": "Local evidence.",
            "products": [{
                "name": "Desk <one>",
                "status": "mixed",
                "evidence": [{"measure": "natural cases", "result": "5 / 10", "note": "small set"}],
            }],
            "findings": ["One <finding>"],
            "limits": ["No production traffic."],
            "framework_checks": [],
        }
        rendered = render_portfolio_html(payload)
        self.assertIn("Support &lt;portfolio&gt;", rendered)
        self.assertIn("Desk &lt;one&gt;", rendered)
        self.assertIn("5 / 10", rendered)
        self.assertNotIn("Desk <one>", rendered)

    def test_report_is_self_contained_and_writable(self):
        payload = {"products": [], "findings": [], "limits": [], "framework_checks": []}
        rendered = render_portfolio_html(payload)
        self.assertIn("<style>", rendered)
        self.assertIn("<script>", rendered)
        with tempfile.TemporaryDirectory() as directory:
            path = write_portfolio_html(Path(directory) / "portfolio.html", payload)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
