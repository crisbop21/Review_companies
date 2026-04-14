"""Memo page — view the most recent IC memo."""

from __future__ import annotations

from ui_components.secrets_bridge import push_secrets_to_env

push_secrets_to_env()

import streamlit as st  # noqa: E402

from ui_components.memo_card import render_memo  # noqa: E402

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
