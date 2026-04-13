"""Unit tests for decision validation. No API calls."""

from __future__ import annotations

import pytest

from pipeline.step8_decision import create_decision


def test_valid_decision() -> None:
    d = create_decision(
        action="buy",
        conviction=7,
        rationale="Bull score 8, margin expansion supported by structural tailwinds.",
        price=412.55,
        size_pct=3.0,
    )
    assert d["action"] == "buy"
    assert d["conviction"] == 7
    assert d["size_pct"] == 3.0


@pytest.mark.parametrize("action", ["yolo", "sell", "", "BUY "])
def test_invalid_action(action: str) -> None:
    with pytest.raises(ValueError):
        create_decision(action=action, conviction=5, rationale="ok")


@pytest.mark.parametrize("conviction", [0, 11, -1, 100])
def test_invalid_conviction(conviction: int) -> None:
    with pytest.raises(ValueError):
        create_decision(action="buy", conviction=conviction, rationale="ok")


def test_empty_rationale() -> None:
    with pytest.raises(ValueError):
        create_decision(action="hold", conviction=5, rationale="   ")


def test_negative_price() -> None:
    with pytest.raises(ValueError):
        create_decision(action="buy", conviction=5, rationale="ok", price=-1.0)


def test_size_pct_out_of_range() -> None:
    with pytest.raises(ValueError):
        create_decision(action="buy", conviction=5, rationale="ok", size_pct=150)
