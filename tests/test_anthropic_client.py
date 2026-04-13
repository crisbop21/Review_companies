"""Unit tests for the AnthropicClient helpers. No live API calls."""

from __future__ import annotations

import pytest

from pipeline.utils.anthropic_client import _extract_json, _concat_text_blocks


class _FakeBlock:
    def __init__(self, text: str) -> None:
        self.text = text


def test_concat_text_blocks_joins_text_pieces() -> None:
    blocks = [_FakeBlock("Hello "), _FakeBlock("world.")]
    assert _concat_text_blocks(blocks) == "Hello world."


def test_concat_text_blocks_ignores_non_text() -> None:
    class _ToolBlock:
        name = "web_search"

    blocks = [_FakeBlock("Hello"), _ToolBlock(), _FakeBlock(" world")]
    assert _concat_text_blocks(blocks) == "Hello world"


def test_extract_json_plain() -> None:
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced() -> None:
    fenced = """Here is the result:
```json
{"a": 1, "b": [2, 3]}
```
"""
    assert _extract_json(fenced) == {"a": 1, "b": [2, 3]}


def test_extract_json_plain_fence() -> None:
    fenced = "```\n{\"x\": true}\n```"
    assert _extract_json(fenced) == {"x": True}


def test_extract_json_invalid_raises() -> None:
    with pytest.raises(Exception):
        _extract_json("not json at all")
