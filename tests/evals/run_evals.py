"""Eval harness: score a pipeline-step fixture against its rubric.

Usage::

    python -m tests.evals.run_evals --step step1_ingest --fixture msft_q1_2026

For each rubric, the harness asks Claude Opus (the judge model) to score
each criterion 1–5 with a one-sentence justification. Scores are
weighted-averaged; the rubric's ``pass_threshold`` determines pass/fail.

Scorecards are printed to stdout and written under ``tests/evals/runs/``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pipeline.utils.anthropic_client import AnthropicClient

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
RUNS_DIR = Path(__file__).resolve().parent / "runs"


@dataclass
class CriterionScore:
    id: str
    weight: float
    score: int
    evidence: str


@dataclass
class Scorecard:
    step: str
    fixture: str
    rubric_version: str
    pass_threshold: float
    scores: list[CriterionScore] = field(default_factory=list)

    @property
    def weighted_average(self) -> float:
        return sum(s.score * s.weight for s in self.scores)

    @property
    def passed(self) -> bool:
        return self.weighted_average >= self.pass_threshold

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "fixture": self.fixture,
            "rubric_version": self.rubric_version,
            "pass_threshold": self.pass_threshold,
            "weighted_average": round(self.weighted_average, 3),
            "passed": self.passed,
            "scores": [
                {
                    "id": s.id,
                    "weight": s.weight,
                    "score": s.score,
                    "evidence": s.evidence,
                }
                for s in self.scores
            ],
        }


_JUDGE_SYSTEM = """You are a strict evaluator. For each criterion you
receive, return a score from 1 to 5 according to the provided scale and a
one-sentence justification citing specific evidence from the fixture.

Return JSON only in this shape:

{"id": "...", "score": 1-5, "evidence": "..."}"""


def _score_criterion(
    client: AnthropicClient,
    fixture_json: str,
    criterion: dict[str, Any],
) -> CriterionScore:
    user = (
        f"Criterion id: {criterion['id']}\n"
        f"Question: {criterion['question']}\n"
        f"Scale:\n{yaml.safe_dump(criterion['scale'], sort_keys=False)}\n\n"
        f"Fixture:\n{fixture_json}\n\n"
        "Return JSON only."
    )
    result = client.complete(
        tier="opus",
        system=_JUDGE_SYSTEM,
        user=user,
        max_tokens=400,
        temperature=0.0,
    )
    parsed = result.as_json()
    return CriterionScore(
        id=criterion["id"],
        weight=float(criterion["weight"]),
        score=int(parsed["score"]),
        evidence=str(parsed.get("evidence", "")),
    )


def run_eval(step: str, fixture: str) -> Scorecard:
    rubric_path = RUBRICS_DIR / f"{step}_rubric.yaml"
    fixture_path = FIXTURES_DIR / step / f"{fixture}.json"

    if not rubric_path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_path}")
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    rubric = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    fixture_text = fixture_path.read_text(encoding="utf-8")

    client = AnthropicClient()
    card = Scorecard(
        step=step,
        fixture=fixture,
        rubric_version=str(rubric.get("version", "unknown")),
        pass_threshold=float(rubric["pass_threshold"]),
    )
    for c in rubric["criteria"]:
        card.scores.append(_score_criterion(client, fixture_text, c))
    return card


def _write_scorecard(card: Scorecard) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%S")
    out = RUNS_DIR / f"{card.step}__{card.fixture}__{ts}.json"
    out.write_text(json.dumps(card.to_dict(), indent=2), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pipeline-step evals.")
    parser.add_argument("--step", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args(argv)

    try:
        card = run_eval(args.step, args.fixture)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(card.to_dict(), indent=2))
    path = _write_scorecard(card)
    print(f"\nScorecard written to: {path}", file=sys.stderr)
    return 0 if card.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
