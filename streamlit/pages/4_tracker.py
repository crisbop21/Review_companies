"""Tracker page — run the thesis tracker against the prior quarter."""

from __future__ import annotations

import json

import streamlit as st

from pipeline.orchestrator import run_pipeline
from pipeline.utils.supabase_client import SupabasePipelineClient

st.title("Thesis Tracker")

st.markdown(
    """
This page compares the most-recent run for a company to the prior memo and
emits a delta report: what changed, which assumptions held, which kill
conditions (if any) triggered.
"""
)

ticker = st.text_input("Ticker", value="MSFT").strip().upper()
quarter = st.text_input("Current quarter tag", value="Q1_2026").strip()
transcript = st.text_area("Current-quarter transcript", height=250)

if st.button("Run tracker", type="primary", disabled=not transcript):
    sb = SupabasePipelineClient()
    company = sb.get_or_create_company(ticker, ticker)
    prior = sb.get_prior_run(company["id"])
    if not prior:
        st.error("No prior run found for this company. Generate a memo first.")
        st.stop()

    prior_outputs = {
        "claims_concepts": prior.get("claims_json"),
        "explanations": prior.get("explanations_json"),
        "critiques": prior.get("critiques_json"),
        "sector": prior.get("sector_context_json"),
    }
    prior_memo = prior.get("memo")  # If memo was stored inline; otherwise fetch.

    with st.status("Running pipeline + tracker…", expanded=True) as status:
        try:
            result = run_pipeline(
                source=transcript,
                source_type="text",
                ticker=ticker,
                quarter=quarter,
                prior_memo=prior_memo,
                prior_outputs=prior_outputs,
            )
        except Exception as exc:
            status.update(label=f"Tracker failed: {exc}", state="error")
            st.stop()
        status.update(label="Tracker complete.", state="complete")

    if not result.review:
        st.warning("No delta report produced (no prior memo found).")
    else:
        st.subheader("Recommended action")
        action = result.review.get("recommended_action", "?")
        st.metric("Action", action.upper())

        st.subheader("Thesis intact?")
        st.success("Yes") if result.review.get("thesis_still_intact") else st.error("No")

        st.subheader("Narrative")
        st.write(result.review.get("review_text", ""))

        st.subheader("Detail")
        st.json(result.review)
