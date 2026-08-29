import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from support_evals.cli import main


class CliEndToEndTests(unittest.TestCase):
    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        return code, json.loads(output.getvalue())

    def test_list_and_plan_show_reference_adapters_and_support_profile(self):
        code, listing = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("fixture", listing["adapters"])
        self.assertIn("reference-shop", listing["adapters"])
        self.assertIn("reference-voice", listing["adapters"])

        code, plan = self.run_cli("plan", "--adapter", "reference-shop")
        self.assertEqual(code, 0)
        self.assertEqual(plan["requested"], 5)
        self.assertIn("answer-policy", plan["evaluators"])
        self.assertIn("unsafe-adversarial", plan["evaluators"])

    def test_reference_shop_writes_json_and_html(self):
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "shop.json"
            html_path = Path(directory) / "shop.html"
            code, payload = self.run_cli(
                "run", "--adapter", "reference-shop", "--output", str(json_path), "--html", str(html_path)
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["counts"]["requested"], 5)
            self.assertTrue(payload["release_gate"]["passed"])
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())
            self.assertIn("READY TO RELEASE", html_path.read_text(encoding="utf-8"))

    def test_reference_shop_mutation_fails_with_unsafe_result(self):
        code, payload = self.run_cli("run", "--adapter", "reference-shop", "--mutation", "unsafe-promise")
        self.assertEqual(code, 1)
        self.assertGreaterEqual(payload["counts"]["unsafe"], 1)
        self.assertFalse(payload["release_gate"]["passed"])

    def test_voice_capture_uses_same_report_shape_and_strict_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "voice.json"
            html_path = Path(directory) / "voice.html"
            code, payload = self.run_cli(
                "run", "--adapter", "reference-voice", "--case", "passing", "--output", str(json_path), "--html", str(html_path)
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["profile"], "voice-strict")
            self.assertEqual(payload["counts"]["requested"], 1)
            self.assertTrue(payload["release_gate"]["passed"])
            self.assertTrue(html_path.exists())

        code, payload = self.run_cli("run", "--adapter", "reference-voice", "--case", "broken-action")
        self.assertEqual(code, 1)
        self.assertFalse(payload["release_gate"]["passed"])
        self.assertGreater(
            sum(payload["counts"][key] for key in ("failed", "error", "abstention", "unsafe")),
            0,
        )

    def test_langfuse_dry_run_writes_payload_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "langfuse.json"
            code, _ = self.run_cli(
                "run", "--adapter", "reference-shop", "--langfuse-dry-run", "--langfuse-output", str(path)
            )
            self.assertEqual(code, 0)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["metadata"]["source"], "support-evals")
            self.assertTrue(payload["batch"])


if __name__ == "__main__":
    unittest.main()
