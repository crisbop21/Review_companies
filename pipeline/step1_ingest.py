"""Step 1: Transcript ingestion.

Accepts raw text, a PDF path, or a ticker. Produces structured JSON:
claims + concept_glossary. See prompts/step1_transcript_ingestion.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def _load_pdf_text(pdf_path: str) -> str:
    import pdfplumber  # local import: pdfplumber is optional at install time

    parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


def _fetch_by_ticker(ticker: str, client: AnthropicClient) -> str:
    """Ask Claude's web_search tool to retrieve the most recent earnings
    transcript for ``ticker``. Used only for the ``source_type='ticker'``
    entry point."""
    result = client.complete(
        tier="sonnet",
        system=(
            "You are a research assistant. Use web_search to find the most "
            "recent full earnings-call transcript for the given ticker and "
            "return ONLY the transcript text, no commentary."
        ),
        user=f"Ticker: {ticker}. Find and return the most recent earnings transcript.",
        max_tokens=16_000,
        web_search=True,
    )
    return result.text


def run(
    source: str,
    source_type: str = "text",
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    """Run Step 1 and return ``(output, prompt)``.

    Args:
        source: Raw transcript text, path to a PDF, or a ticker symbol.
        source_type: One of ``"text"``, ``"pdf"``, ``"ticker"``.
    """
    client = client or AnthropicClient()

    if source_type == "text":
        transcript = source
    elif source_type == "pdf":
        transcript = _load_pdf_text(source)
    elif source_type == "ticker":
        transcript = _fetch_by_ticker(source, client)
    else:
        raise ValueError(f"Unknown source_type: {source_type!r}")

    if not transcript.strip():
        raise ValueError("Empty transcript — refusing to call the model.")

    prompt = load_prompt("step1_transcript_ingestion")
    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=f"Transcript:\n\n{transcript}",
        max_tokens=8_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
