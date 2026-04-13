"""Memo page — view the most recent IC memo."""

from __future__ import annotations

import streamlit as st

from ui_components.memo_card import render_memo

st.title("IC Memo")

memo = st.session_state.get("last_memo")
if not memo:
    st.info(
        "No memo in session yet. Run the pipeline on the **Generate** page "
        "to populate it."
    )
else:
    render_memo(memo)
    st.download_button(
        "Download memo (JSON)",
        data=__import__("json").dumps(memo, indent=2),
        file_name="memo.json",
    )
