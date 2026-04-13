# Eval harness

Runs rubrics against frozen pipeline outputs so prompt-version changes are
measurable rather than vibes-based.

## Why it exists

The pipeline has six prompt-driven steps (1, 2, 3, 4, 5, 7, 9). Each is likely
to go through dozens of iterations. Without a harness, you silently regress.
With one, every prompt PR includes a scorecard diff, and the first sign of a
regression is a failing number not a missed podcast.

## Layout

```
tests/evals/
├── rubrics/        # one YAML per step (pass threshold + weighted criteria)
├── fixtures/       # frozen pipeline outputs, per step, per ticker/quarter
├── runs/           # gitignored: judged scorecards from local runs
└── run_evals.py    # entry point
```

## Workflow

1. Land a prompt change in `prompts/stepN_*.md` and bump its `version:` in the
   frontmatter.
2. Regenerate the fixture you want to test against by running the step on a
   test transcript and committing the JSON under
   `tests/evals/fixtures/<step>/`.
3. Run `python -m tests.evals.run_evals --step stepN_... --fixture <name>`.
4. Compare the printed scorecard to the previous run. Check the diff into the
   PR description.

## Judge model

Claude Opus. Sonnet is too lenient as a judge on analytical rubrics.
Opus costs roughly $0.015 per criterion on a short fixture — cheap relative
to the cost of a regressed prompt shipping.

## What's here today

- `rubrics/step1_claims_rubric.yaml` — first worked example.
- `run_evals.py` — CLI + fixture-loading scaffold. Scoring logic is stubbed
  until the first prompt PR (Task 1.2) lands the Step 1 prompt and a fixture.
