"""Memo rendering component."""

from __future__ import annotations

import streamlit as st


def render_memo(memo: dict) -> None:
    thesis = memo.get("thesis_summary", "—")
    bull = memo.get("bull_score", "—")
    bear = memo.get("bear_score", "—")
    size = memo.get("suggested_size_pct", "—")
    horizon = memo.get("time_horizon", "—")

    st.subheader("Thesis")
    st.write(thesis)

    cols = st.columns(4)
    cols[0].metric("Bull", bull)
    cols[1].metric("Bear", bear)
    cols[2].metric("Size %", size)
    cols[3].metric("Horizon", horizon)

    st.subheader("Assumptions")
    for a in memo.get("key_assumptions", []):
        with st.container(border=True):
            st.markdown(f"**{a.get('text', '')}**")
            st.caption(f"Confidence {a.get('confidence', '?')} / 10")
            rationale = a.get("rationale")
            if rationale:
                st.write(rationale)

    st.subheader("Kill conditions")
    for k in memo.get("kill_conditions", []):
        with st.container(border=True):
            st.markdown(f"**{k.get('condition_text', '')}**")
            cols = st.columns(3)
            cols[0].text(f"metric: {k.get('metric_name', '—')}")
            cols[1].text(f"threshold: {k.get('threshold_value', '—')}")
            cols[2].text(f"direction: {k.get('threshold_direction', '—')}")

    st.subheader("Memo")
    st.write(memo.get("memo_text", ""))
