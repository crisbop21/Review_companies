"""Decision form component."""

from __future__ import annotations

import streamlit as st

from pipeline.step8_decision import create_decision
from pipeline.utils.supabase_client import SupabasePipelineClient


def render_decision_form(company_id: str, memo: dict) -> None:
    st.markdown(
        "Log a decision. Decisions are append-only — no edits, no deletes."
    )

    with st.form("decision_form"):
        action = st.selectbox(
            "Action", ["buy", "add", "trim", "exit", "pass", "hold"]
        )
        conviction = st.slider("Conviction", 1, 10, 5)
        default_size = float(memo.get("suggested_size_pct") or 0.0)
        size = st.number_input(
            "Position size %", min_value=0.0, max_value=100.0, value=default_size,
            step=0.1,
        )
        price = st.number_input(
            "Price at decision", min_value=0.0, value=0.0, step=0.01
        )
        rationale = st.text_area(
            "Rationale", placeholder="Why this action, in your own words."
        )
        memo_id = st.session_state.get("last_memo_id")
        submitted = st.form_submit_button("Record decision", type="primary")

    if submitted:
        try:
            decision = create_decision(
                action=action,
                conviction=int(conviction),
                rationale=rationale,
                price=price or None,
                size_pct=size or None,
                memo_id=memo_id,
            )
        except ValueError as exc:
            st.error(f"Invalid decision: {exc}")
            return

        try:
            sb = SupabasePipelineClient()
            result = sb.save_decision(company_id, decision)
            st.success(f"Decision recorded: {result.get('id', '')}")
            st.json(result)
        except Exception as exc:
            st.error(f"Failed to persist decision: {exc}")
