"""Step 8: Decision log. Validates and constructs decision records.

Step 8 is NOT automatic. The orchestrator surfaces the memo and waits for
the user to make a decision (via the UI or CLI). This module is pure
validation + record construction; persistence is handled by
``pipeline.utils.supabase_client``.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

Action = Literal["buy", "add", "trim", "exit", "pass", "hold"]
_ALLOWED_ACTIONS: tuple[str, ...] = ("buy", "add", "trim", "exit", "pass", "hold")


def create_decision(
    action: str,
    conviction: int,
    rationale: str,
    price: float | None = None,
    size_pct: float | None = None,
    decision_date: date | None = None,
    memo_id: str | None = None,
) -> dict:
    """Return a validated decision record ready for insert.

    Raises ``ValueError`` if any field is invalid.
    """
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(
            f"action must be one of {_ALLOWED_ACTIONS}, got {action!r}"
        )
    if not isinstance(conviction, int) or not 1 <= conviction <= 10:
        raise ValueError("conviction must be an int between 1 and 10")
    if not rationale or not rationale.strip():
        raise ValueError("rationale is required")
    if size_pct is not None and not 0 <= size_pct <= 100:
        raise ValueError("size_pct must be between 0 and 100")
    if price is not None and price < 0:
        raise ValueError("price must be non-negative")

    return {
        "action": action,
        "conviction": conviction,
        "rationale": rationale.strip(),
        "size_pct": size_pct,
        "price_at_decision": price,
        "decision_date": (decision_date or date.today()).isoformat(),
        "memo_id": memo_id,
    }
