#!/usr/bin/env python3
"""Render a support-leader HTML view from a portfolio evidence JSON file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from support_evals.portfolio import load_portfolio_json, write_portfolio_html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    write_portfolio_html(args.output, load_portfolio_json(args.input))


if __name__ == "__main__":
    main()
