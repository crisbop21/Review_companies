"""Pipeline orchestrator. Wires Steps 1-9 into a sequential run.

Implementation lands in Phase 1 Task 1.7. This file is a stub so that CLI
entry points and tests can import it during scaffolding.
"""

from __future__ import annotations


def run_pipeline(transcript: str, source_type: str = "text") -> dict:
    """Run the full Steps 1-9 pipeline.

    Args:
        transcript: Raw transcript text, PDF path, or ticker string.
        source_type: One of ``text``, ``pdf``, ``ticker``.

    Returns:
        Dictionary with all intermediate step outputs plus the final script.
    """
    raise NotImplementedError("Orchestrator is implemented in Phase 1 Task 1.7.")


if __name__ == "__main__":
    raise SystemExit(
        "Orchestrator CLI is not yet wired. See IMPLEMENTATION_PLAN.md Task 1.7."
    )
