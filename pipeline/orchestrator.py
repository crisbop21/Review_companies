"""Pipeline orchestrator.

Wires Steps 1–7 (+9 on repeat runs) into a sequential run with progress
logging, partial-output preservation on failure, and Supabase persistence.

Step 6 (audio) and Step 8 (decision) are opt-in:
- ``--audio`` renders MP3s via ElevenLabs.
- Step 8 is user-initiated; the orchestrator surfaces the memo and exits.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline import (
    step1_ingest,
    step2_decode,
    step3_critique,
    step4_sector,
    step5_script,
    step6_audio,
    step7_memo,
    step9_tracker,
)
from pipeline.config import Config
from pipeline.utils import chunker
from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    ticker: str
    quarter: str
    step1: dict | None = None
    step2: dict | None = None
    step3: dict | None = None
    step4: dict | None = None
    script_en: str | None = None
    script_es: str | None = None
    audio_en_path: str | None = None
    audio_es_path: str | None = None
    memo: dict | None = None
    review: dict | None = None
    chunks: list[dict] = field(default_factory=list)
    prompt_versions: dict[str, str] = field(default_factory=dict)
    model_versions: dict[str, str] = field(default_factory=dict)
    step_durations: dict[str, float] = field(default_factory=dict)
    failed_step: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "quarter": self.quarter,
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4,
            "script_en": self.script_en,
            "script_es": self.script_es,
            "audio_en_path": self.audio_en_path,
            "audio_es_path": self.audio_es_path,
            "memo": self.memo,
            "review": self.review,
            "chunks_count": len(self.chunks),
            "prompt_versions": self.prompt_versions,
            "model_versions": self.model_versions,
            "step_durations": self.step_durations,
            "failed_step": self.failed_step,
            "error": self.error,
        }


def _record_prompt(result: PipelineResult, prompt: Prompt) -> None:
    result.prompt_versions[prompt.name] = prompt.version
    result.model_versions[prompt.name] = prompt.model_tier


def _timed(result: PipelineResult, step_name: str, fn, *args, **kwargs):
    logger.info("step=%s starting", step_name)
    start = time.monotonic()
    try:
        output = fn(*args, **kwargs)
    except Exception as exc:
        elapsed = time.monotonic() - start
        result.step_durations[step_name] = elapsed
        result.failed_step = step_name
        result.error = f"{type(exc).__name__}: {exc}"
        logger.exception("step=%s failed after %.1fs", step_name, elapsed)
        raise
    elapsed = time.monotonic() - start
    result.step_durations[step_name] = elapsed
    logger.info("step=%s done in %.1fs", step_name, elapsed)
    return output


def run_pipeline(
    source: str,
    *,
    source_type: str = "text",
    ticker: str = "UNKNOWN",
    quarter: str = "UNKNOWN",
    audio: bool = False,
    spanish: bool = False,
    prior_memo: dict | None = None,
    prior_outputs: dict | None = None,
    anthropic: AnthropicClient | None = None,
    audio_output_dir: str = "out",
) -> PipelineResult:
    """Run Steps 1–7 (+9 if prior data is provided).

    Args:
        source: transcript text, PDF path, or ticker (per ``source_type``).
        source_type: ``"text"``, ``"pdf"``, or ``"ticker"``.
        ticker/quarter: provenance labels written to chunks + Supabase.
        audio: if True, generate EN audio (and ES if ``spanish`` is also True).
        spanish: if True, also adapt + (optionally) synthesize the ES version.
        prior_memo: prior-quarter IC memo dict. If provided, Step 9 runs.
        prior_outputs: prior-quarter upstream outputs for Step 9 context.
    """
    anthropic = anthropic or AnthropicClient()
    result = PipelineResult(ticker=ticker, quarter=quarter)

    try:
        step1_out, p1 = _timed(
            result, "step1_ingest",
            step1_ingest.run, source, source_type, anthropic,
        )
        result.step1 = step1_out
        _record_prompt(result, p1)

        # Keep the raw transcript for Step 4 regardless of source_type.
        if source_type == "text":
            transcript_text = source
        elif source_type == "pdf":
            transcript_text = step1_ingest._load_pdf_text(source)
        else:
            transcript_text = json.dumps(step1_out)  # best-effort fallback

        step2_out, p2 = _timed(
            result, "step2_decode",
            step2_decode.run, step1_out, anthropic,
        )
        result.step2 = step2_out
        _record_prompt(result, p2)

        step3_out, p3 = _timed(
            result, "step3_critique",
            step3_critique.run, step1_out, anthropic,
        )
        result.step3 = step3_out
        _record_prompt(result, p3)

        step4_out, p4 = _timed(
            result, "step4_sector",
            step4_sector.run, transcript_text, anthropic,
        )
        result.step4 = step4_out
        _record_prompt(result, p4)

        script_en, p5 = _timed(
            result, "step5_script",
            step5_script.run, step1_out, step2_out, step3_out, step4_out, anthropic,
        )
        result.script_en = script_en
        _record_prompt(result, p5)

        if spanish:
            script_es, p5b = _timed(
                result, "step5b_spanish",
                step5_script.adapt_spanish, script_en, anthropic,
            )
            result.script_es = script_es
            _record_prompt(result, p5b)

        memo, p7 = _timed(
            result, "step7_memo",
            step7_memo.run,
            {
                "claims_concepts": step1_out,
                "explanations": step2_out,
                "critiques": step3_out,
                "sector": step4_out,
            },
            anthropic,
        )
        result.memo = memo
        _record_prompt(result, p7)

        if prior_memo is not None and prior_outputs is not None:
            review, p9 = _timed(
                result, "step9_tracker",
                step9_tracker.run,
                {
                    "claims_concepts": step1_out,
                    "explanations": step2_out,
                    "critiques": step3_out,
                    "sector": step4_out,
                    "memo": memo,
                },
                prior_memo,
                prior_outputs,
                anthropic,
            )
            result.review = review
            _record_prompt(result, p9)

        if audio and script_en:
            out_dir = Path(audio_output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            en_path = out_dir / f"{ticker}_{quarter}_en.mp3"
            result.audio_en_path = _timed(
                result, "step6_audio_en",
                step6_audio.run, script_en, str(en_path), "en",
            )
            if spanish and result.script_es:
                es_path = out_dir / f"{ticker}_{quarter}_es.mp3"
                result.audio_es_path = _timed(
                    result, "step6_audio_es",
                    step6_audio.run, result.script_es, str(es_path), "es",
                )

        # Chunker runs last so every upstream output is available.
        result.chunks = chunker.chunk_all(
            ticker=ticker,
            quarter=quarter,
            step1=step1_out,
            step2=step2_out,
            step3=step3_out,
            step4=step4_out,
            memo=memo,
            review=result.review,
        )

    except Exception:
        # Partial result is already populated; re-raise so callers can see it.
        raise

    return result


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the earnings-podcast pipeline.")
    parser.add_argument("--ticker", required=True, help="Company ticker.")
    parser.add_argument("--quarter", required=True, help='Quarter tag, e.g. "Q1_2026".')
    parser.add_argument("--transcript", help="Path to a transcript text file.")
    parser.add_argument("--pdf", help="Path to a transcript PDF file.")
    parser.add_argument("--audio", action="store_true", help="Render audio.")
    parser.add_argument("--spanish", action="store_true", help="Also produce Spanish version.")
    parser.add_argument("--out", default="out", help="Output directory.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    _configure_logging(args.log_level)

    if args.transcript:
        source = Path(args.transcript).read_text(encoding="utf-8")
        source_type = "text"
    elif args.pdf:
        source = args.pdf
        source_type = "pdf"
    else:
        source = args.ticker
        source_type = "ticker"

    start = time.monotonic()
    result = run_pipeline(
        source=source,
        source_type=source_type,
        ticker=args.ticker,
        quarter=args.quarter,
        audio=args.audio,
        spanish=args.spanish,
        audio_output_dir=args.out,
    )
    total = time.monotonic() - start

    summary = result.as_dict()
    summary["total_duration_seconds"] = round(total, 1)
    print(json.dumps(summary, indent=2, default=str))
    return 0 if result.failed_step is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
