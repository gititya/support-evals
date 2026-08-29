"""Local, dependency-free report writers for Support Evals."""

from .report import build_report_payload, render_html, write_html, write_json

__all__ = ["build_report_payload", "render_html", "write_html", "write_json"]
