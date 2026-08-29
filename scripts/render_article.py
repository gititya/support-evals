#!/usr/bin/env python3
"""Render the article-style support-evaluation brief."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from support_evals.article import write_article_html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    write_article_html(args.output, payload)


if __name__ == "__main__":
    main()
