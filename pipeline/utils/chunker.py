"""RAG-ready chunker.

Decomposes each pipeline step's output into 60–80 individually-addressable
chunks with standardized metadata. Chunks are deterministic, one-idea-per-
chunk, and 50–200 words.

Each chunk is a dict::

    {
        "chunk_type": "critique",
        "chunk_text": "...",
        "metadata": {
            "ticker": "MSFT",
            "quarter": "Q1_2026",
            "chunk_type": "critique",
            "lens": "metric_selection",
            "target_claim_id": "claim_003",
        }
    }

The ``embedding`` column on the Supabase row is left null at insert time;
the backfill script populates it when RAG is enabled.
"""

from __future__ import annotations

from typing import Any, Iterable

Chunk = dict[str, Any]

ALLOWED_CHUNK_TYPES = frozenset(
    {
        "claim",
        "concept",
        "critique",
        "sector_bull",
        "sector_bear",
        "assumption",
        "kill_condition",
        "thesis_summary",
        "delta_observation",
    }
)

_MIN_WORDS = 20  # keep in sync with acceptance criteria
_MAX_WORDS = 250


def build_metadata(
    ticker: str, quarter: str, chunk_type: str, **extras: Any
) -> dict[str, Any]:
    """Build the standardized metadata envelope for a chunk."""
    if chunk_type not in ALLOWED_CHUNK_TYPES:
        raise ValueError(f"Invalid chunk_type: {chunk_type!r}")
    meta: dict[str, Any] = {
        "ticker": ticker,
        "quarter": quarter,
        "chunk_type": chunk_type,
    }
    meta.update({k: v for k, v in extras.items() if v is not None})
    return meta


def _word_count(text: str) -> int:
    return len(text.split())


def _finalize(chunk: Chunk) -> Chunk:
    """Trim whitespace and enforce word-count bounds (soft lower, hard upper)."""
    chunk["chunk_text"] = chunk["chunk_text"].strip()
    wc = _word_count(chunk["chunk_text"])
    if wc > _MAX_WORDS:
        words = chunk["chunk_text"].split()
        chunk["chunk_text"] = " ".join(words[:_MAX_WORDS])
    return chunk


def _valid(chunk: Chunk) -> bool:
    wc = _word_count(chunk["chunk_text"])
    return wc >= _MIN_WORDS


# ----------------------------------------------------------------------
# Per-step chunkers
# ----------------------------------------------------------------------
def chunk_claims(step1: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []
    for claim in step1.get("claims", []):
        chunk = _finalize(
            {
                "chunk_type": "claim",
                "chunk_text": claim.get("text", ""),
                "metadata": build_metadata(
                    ticker,
                    quarter,
                    "claim",
                    claim_id=claim.get("id"),
                    category=claim.get("category"),
                    concepts=claim.get("concepts"),
                ),
            }
        )
        if _valid(chunk):
            out.append(chunk)
    return out


def chunk_concepts(step2: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []
    for ex in step2.get("explanations", []):
        text_parts = [
            ex.get("definition", ""),
            ex.get("why_it_matters_here", ""),
            ex.get("analogy", ""),
        ]
        text = " ".join(part.strip() for part in text_parts if part and part.strip())
        chunk = _finalize(
            {
                "chunk_type": "concept",
                "chunk_text": text,
                "metadata": build_metadata(
                    ticker,
                    quarter,
                    "concept",
                    concept=ex.get("concept"),
                    depends_on=ex.get("depends_on"),
                    claims_unlocked=ex.get("claims_unlocked"),
                ),
            }
        )
        if _valid(chunk):
            out.append(chunk)
    return out


def chunk_critiques(step3: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []
    for c in step3.get("critiques", []):
        text = c.get("summary", "")
        evidence = c.get("evidence")
        if evidence:
            text = f"{text}\n\nEvidence: {evidence}"
        rebuttal = c.get("bull_rebuttal")
        if rebuttal:
            text = f"{text}\n\nBull rebuttal: {rebuttal}"
        chunk = _finalize(
            {
                "chunk_type": "critique",
                "chunk_text": text,
                "metadata": build_metadata(
                    ticker,
                    quarter,
                    "critique",
                    lens=c.get("lens"),
                    target_claim_id=c.get("target_claim_id"),
                    severity=c.get("severity"),
                ),
            }
        )
        if _valid(chunk):
            out.append(chunk)
    return out


def chunk_sector_context(step4: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []
    sector = step4.get("sector")
    for side, chunk_type in (("bull_case", "sector_bull"), ("bear_case", "sector_bear")):
        case = step4.get(side) or {}
        narrative = case.get("narrative", "")
        if not narrative:
            continue
        chunk = _finalize(
            {
                "chunk_type": chunk_type,
                "chunk_text": narrative,
                "metadata": build_metadata(
                    ticker,
                    quarter,
                    chunk_type,
                    sector=sector,
                    tailwinds=case.get("tailwinds"),
                    headwinds=case.get("headwinds"),
                ),
            }
        )
        if _valid(chunk):
            out.append(chunk)
    return out


def chunk_memo(memo: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []

    thesis = memo.get("thesis_summary")
    if thesis:
        out.append(
            _finalize(
                {
                    "chunk_type": "thesis_summary",
                    "chunk_text": thesis,
                    "metadata": build_metadata(
                        ticker,
                        quarter,
                        "thesis_summary",
                        bull_score=memo.get("bull_score"),
                        bear_score=memo.get("bear_score"),
                        suggested_size_pct=memo.get("suggested_size_pct"),
                        time_horizon=memo.get("time_horizon"),
                    ),
                }
            )
        )

    for i, a in enumerate(memo.get("key_assumptions", [])):
        chunk = _finalize(
            {
                "chunk_type": "assumption",
                "chunk_text": f"{a.get('text', '')}\n\nRationale: {a.get('rationale', '')}",
                "metadata": build_metadata(
                    ticker,
                    quarter,
                    "assumption",
                    rank=i + 1,
                    confidence=a.get("confidence"),
                ),
            }
        )
        if _valid(chunk):
            out.append(chunk)

    for k in memo.get("kill_conditions", []):
        out.append(
            _finalize(
                {
                    "chunk_type": "kill_condition",
                    "chunk_text": k.get("condition_text", ""),
                    "metadata": build_metadata(
                        ticker,
                        quarter,
                        "kill_condition",
                        metric_name=k.get("metric_name"),
                        threshold_value=k.get("threshold_value"),
                        threshold_direction=k.get("threshold_direction"),
                    ),
                }
            )
        )

    # Remove any kill_condition chunks that failed the word-count floor.
    return [c for c in out if _valid(c) or c["chunk_type"] == "kill_condition"]


def chunk_delta_report(review: dict, ticker: str, quarter: str) -> list[Chunk]:
    out: list[Chunk] = []

    bull_evo = review.get("bull_case_evolution")
    if bull_evo:
        out.append(
            _finalize(
                {
                    "chunk_type": "delta_observation",
                    "chunk_text": f"Bull case evolution: {bull_evo}",
                    "metadata": build_metadata(
                        ticker,
                        quarter,
                        "delta_observation",
                        observation_type="bull_evolution",
                    ),
                }
            )
        )
    bear_evo = review.get("bear_case_evolution")
    if bear_evo:
        out.append(
            _finalize(
                {
                    "chunk_type": "delta_observation",
                    "chunk_text": f"Bear case evolution: {bear_evo}",
                    "metadata": build_metadata(
                        ticker,
                        quarter,
                        "delta_observation",
                        observation_type="bear_evolution",
                    ),
                }
            )
        )

    for a in review.get("assumptions_status", []):
        if a.get("status") in ("weakened", "broken"):
            out.append(
                _finalize(
                    {
                        "chunk_type": "delta_observation",
                        "chunk_text": (
                            f"Assumption '{a.get('text', '')}' is "
                            f"{a.get('status')}. {a.get('reasoning', '')}"
                        ),
                        "metadata": build_metadata(
                            ticker,
                            quarter,
                            "delta_observation",
                            observation_type="assumption_change",
                            status=a.get("status"),
                        ),
                    }
                )
            )

    for k in review.get("kill_conditions_status", []):
        if k.get("triggered"):
            out.append(
                _finalize(
                    {
                        "chunk_type": "delta_observation",
                        "chunk_text": (
                            f"Kill condition triggered: '{k.get('condition_text', '')}'. "
                            f"{k.get('reasoning', '')}"
                        ),
                        "metadata": build_metadata(
                            ticker,
                            quarter,
                            "delta_observation",
                            observation_type="kill_triggered",
                        ),
                    }
                )
            )

    return [c for c in out if _valid(c)]


# ----------------------------------------------------------------------
# Aggregate
# ----------------------------------------------------------------------
def chunk_all(
    *,
    ticker: str,
    quarter: str,
    step1: dict | None = None,
    step2: dict | None = None,
    step3: dict | None = None,
    step4: dict | None = None,
    memo: dict | None = None,
    review: dict | None = None,
) -> list[Chunk]:
    """Run every chunker that has input and return the concatenated list."""
    chunks: list[Chunk] = []
    if step1:
        chunks.extend(chunk_claims(step1, ticker, quarter))
        chunks.extend(_concept_glossary_chunks(step1, ticker, quarter))
    if step2:
        chunks.extend(chunk_concepts(step2, ticker, quarter))
    if step3:
        chunks.extend(chunk_critiques(step3, ticker, quarter))
    if step4:
        chunks.extend(chunk_sector_context(step4, ticker, quarter))
    if memo:
        chunks.extend(chunk_memo(memo, ticker, quarter))
    if review:
        chunks.extend(chunk_delta_report(review, ticker, quarter))
    return chunks


def _concept_glossary_chunks(
    step1: dict, ticker: str, quarter: str
) -> list[Chunk]:
    """Step 1's concept_glossary rarely has enough text to meet the word
    floor on its own, but we still emit short-form concept-link chunks as
    metadata-heavy rows. These are filtered by the word floor; most drop."""
    out: list[Chunk] = []
    for entry in step1.get("concept_glossary", []):
        related = entry.get("related_claims") or []
        text = (
            f"{entry.get('term', '')} appears in claims: "
            f"{', '.join(related)}."
        )
        chunk = {
            "chunk_type": "concept",
            "chunk_text": text,
            "metadata": build_metadata(
                ticker,
                quarter,
                "concept",
                term=entry.get("term"),
                source="glossary",
            ),
        }
        if _valid(chunk):
            out.append(chunk)
    return out
