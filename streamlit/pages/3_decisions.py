"""Decisions page — log a buy/add/trim/exit/pass/hold decision."""

from __future__ import annotations

import streamlit as st

from ui_components.decision_form import render_decision_form

st.title("Decisions")

company_id = st.session_state.get("last_company_id")
memo = st.session_state.get("last_memo")

if not company_id or not memo:
    st.info(
        "No memo in session yet. Run the pipeline on the **Generate** page "
        "first."
    )
else:
    render_decision_form(company_id=company_id, memo=memo)
