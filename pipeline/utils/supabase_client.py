"""Supabase client wrapper for the pipeline.

All persistence goes through this module. The RLS policies in
``supabase/migrations/008_create_rls_policies.sql`` ensure each row
is scoped to the authenticated user.
"""

from __future__ import annotations

import logging
from typing import Any

from pipeline.config import Config

logger = logging.getLogger(__name__)


class SupabasePipelineClient:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        from supabase import create_client  # local import

        self._client = create_client(
            self.config.supabase_url,
            self.config.supabase_anon_key,
        )

    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------
    def get_or_create_company(
        self,
        ticker: str,
        name: str,
        sector: str | None = None,
    ) -> dict[str, Any]:
        existing = (
            self._client.table("companies")
            .select("*")
            .eq("ticker", ticker.upper())
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]

        inserted = (
            self._client.table("companies")
            .insert(
                {
                    "ticker": ticker.upper(),
                    "name": name,
                    "sector": sector,
                }
            )
            .execute()
        )
        return inserted.data[0]

    # ------------------------------------------------------------------
    # Analysis runs
    # ------------------------------------------------------------------
    def save_analysis_run(
        self,
        company_id: str,
        quarter: str,
        transcript_source: str,
        *,
        claims: dict | None = None,
        concepts: dict | None = None,
        explanations: dict | None = None,
        critiques: dict | None = None,
        sector_context: dict | None = None,
        script_en: str | None = None,
        script_es: str | None = None,
        audio_en_url: str | None = None,
        audio_es_url: str | None = None,
        prompt_versions: dict | None = None,
        model_versions: dict | None = None,
        status: str = "complete",
        duration_seconds: int | None = None,
    ) -> dict[str, Any]:
        row = {
            "company_id": company_id,
            "quarter": quarter,
            "transcript_source": transcript_source,
            "claims_json": claims,
            "concepts_json": concepts,
            "explanations_json": explanations,
            "critiques_json": critiques,
            "sector_context_json": sector_context,
            "script_en": script_en,
            "script_es": script_es,
            "audio_en_url": audio_en_url,
            "audio_es_url": audio_es_url,
            "prompt_versions": prompt_versions or {},
            "model_versions": model_versions or {},
            "status": status,
            "duration_seconds": duration_seconds,
        }
        result = self._client.table("analysis_runs").insert(row).execute()
        return result.data[0]

    def get_prior_run(self, company_id: str) -> dict[str, Any] | None:
        result = (
            self._client.table("analysis_runs")
            .select("*")
            .eq("company_id", company_id)
            .eq("status", "complete")
            .order("run_date", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    # ------------------------------------------------------------------
    # IC memos & kill conditions
    # ------------------------------------------------------------------
    def save_ic_memo(
        self,
        run_id: str,
        company_id: str,
        memo: dict,
    ) -> dict[str, Any]:
        row = {
            "run_id": run_id,
            "company_id": company_id,
            "thesis_summary": memo["thesis_summary"],
            "bull_score": memo["bull_score"],
            "bear_score": memo["bear_score"],
            "key_assumptions": memo.get("key_assumptions", []),
            "suggested_size_pct": memo.get("suggested_size_pct"),
            "time_horizon": memo.get("time_horizon"),
            "memo_text": memo["memo_text"],
        }
        result = self._client.table("ic_memos").insert(row).execute()
        return result.data[0]

    def save_kill_conditions(
        self,
        memo_id: str,
        company_id: str,
        conditions: list[dict],
    ) -> list[dict[str, Any]]:
        if not conditions:
            return []
        rows = [
            {
                "memo_id": memo_id,
                "company_id": company_id,
                "condition_text": c["condition_text"],
                "metric_name": c.get("metric_name"),
                "threshold_value": c.get("threshold_value"),
                "threshold_direction": c.get("threshold_direction"),
            }
            for c in conditions
        ]
        result = self._client.table("kill_conditions").insert(rows).execute()
        return result.data

    def get_active_kill_conditions(self, company_id: str) -> list[dict[str, Any]]:
        result = (
            self._client.table("kill_conditions")
            .select("*")
            .eq("company_id", company_id)
            .eq("status", "active")
            .execute()
        )
        return result.data

    def update_kill_condition_status(
        self,
        kill_id: str,
        status: str,
        triggered_by_run_id: str | None = None,
    ) -> dict[str, Any]:
        patch: dict[str, Any] = {"status": status}
        if status == "triggered":
            patch["triggered_at"] = "now()"
            patch["triggered_by_run_id"] = triggered_by_run_id
        result = (
            self._client.table("kill_conditions")
            .update(patch)
            .eq("id", kill_id)
            .execute()
        )
        return result.data[0]

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------
    def save_decision(
        self,
        company_id: str,
        decision: dict,
    ) -> dict[str, Any]:
        row = {"company_id": company_id, **decision}
        result = self._client.table("decisions").insert(row).execute()
        return result.data[0]

    # ------------------------------------------------------------------
    # Thesis reviews
    # ------------------------------------------------------------------
    def save_thesis_review(
        self,
        company_id: str,
        current_run_id: str,
        prior_run_id: str,
        review: dict,
    ) -> dict[str, Any]:
        row = {
            "company_id": company_id,
            "current_run_id": current_run_id,
            "prior_run_id": prior_run_id,
            "guidance_vs_actual": review.get("guidance_vs_actual"),
            "assumptions_status": review.get("assumptions_status"),
            "kill_conditions_status": review.get("kill_conditions_status"),
            "bear_case_evolution": review.get("bear_case_evolution"),
            "bull_case_evolution": review.get("bull_case_evolution"),
            "thesis_still_intact": review["thesis_still_intact"],
            "recommended_action": review["recommended_action"],
            "review_text": review["review_text"],
        }
        result = self._client.table("thesis_reviews").insert(row).execute()
        return result.data[0]

    # ------------------------------------------------------------------
    # Chunks
    # ------------------------------------------------------------------
    def save_chunks(
        self,
        run_id: str,
        company_id: str,
        chunks: list[dict],
    ) -> int:
        """Batch insert chunks. Returns the count inserted."""
        if not chunks:
            return 0
        rows = [
            {
                "run_id": run_id,
                "company_id": company_id,
                "chunk_type": c["chunk_type"],
                "chunk_text": c["chunk_text"],
                "metadata": c["metadata"],
            }
            for c in chunks
        ]
        result = self._client.table("analysis_chunks").insert(rows).execute()
        logger.info("persisted %d chunks for run=%s", len(result.data), run_id)
        return len(result.data)


def get_client() -> SupabasePipelineClient:
    """Module-level convenience constructor."""
    return SupabasePipelineClient()
