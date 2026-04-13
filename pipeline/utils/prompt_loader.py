"""Load prompts from prompts/*.md and expose their YAML frontmatter.

Each prompt file starts with a ``---`` fenced YAML block containing at
least: ``step``, ``name``, ``version``, ``model_tier``, ``web_search``.
The body below the second fence is the system prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    model_tier: str
    web_search: bool
    system: str
    meta: dict[str, Any]


def load_prompt(name: str) -> Prompt:
    """Load ``prompts/<name>.md`` and parse its frontmatter + body."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")

    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Prompt {name} is missing a YAML frontmatter block.")

    meta = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    for key in ("name", "version", "model_tier"):
        if key not in meta:
            raise ValueError(f"Prompt {name} frontmatter missing '{key}'.")

    return Prompt(
        name=str(meta["name"]),
        version=str(meta["version"]),
        model_tier=str(meta["model_tier"]),
        web_search=bool(meta.get("web_search", False)),
        system=body,
        meta=meta,
    )
