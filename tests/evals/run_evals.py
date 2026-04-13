"""Eval harness: run rubrics against frozen pipeline outputs.

Usage (once fixtures and the AnthropicClient are available):

    python -m tests.evals.run_evals --step step1_ingest --fixture msft_q1_2026

For each rubric the harness:

1. Loads the rubric YAML from ``tests/evals/rubrics/``.
2. Loads the matching frozen fixture from ``tests/evals/fixtures/<step>/<name>.json``.
3. Asks the judge model (Opus) to score each criterion 1-5 with evidence.
4. Computes the weighted average and compares to ``pass_threshold``.
5. Writes the scorecard under ``tests/evals/runs/<timestamp>/``.

This file is intentionally unimplemented during the scaffolding PR so that
the very first prompt PR can land the harness alongside the prompt itself.
The module exists to establish the pattern, not to gate CI yet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
RUNS_DIR = Path(__file__).resolve().parent / "runs"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pipeline-step evals.")
    parser.add_argument("--step", required=True, help="e.g. step1_ingest")
    parser.add_argument("--fixture", required=True, help="e.g. msft_q1_2026")
    args = parser.parse_args(argv)

    rubric_path = RUBRICS_DIR / f"{args.step}_rubric.yaml"
    fixture_path = FIXTURES_DIR / args.step / f"{args.fixture}.json"

    if not rubric_path.exists():
        print(f"Rubric not found: {rubric_path}", file=sys.stderr)
        return 2
    if not fixture_path.exists():
        print(f"Fixture not found: {fixture_path}", file=sys.stderr)
        return 2

    raise NotImplementedError(
        "Harness scoring lands with the first prompt PR. See module docstring."
    )


if __name__ == "__main__":
    raise SystemExit(main())
