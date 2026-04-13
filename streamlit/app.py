"""Earnings Podcast Agent — Streamlit entry point.

Run with::

    streamlit run streamlit/app.py

The home page explains the product; individual workflows live on the
numbered pages in ``streamlit/pages/``.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Earnings Podcast Agent",
    page_icon="",
    layout="wide",
)

st.title("Earnings Podcast Agent")
st.markdown(
    """
Turn any company's earnings call into a 45-minute educational podcast with
built-in investment governance.

Three AI voices — a curious **HOST**, a data-driven **BULL**, and a
skeptical **BEAR** — debate the business. On top of the podcast, an IC
memo scores the thesis 1–10, logs decisions, and tracks whether your
thesis is still intact quarter over quarter.

Use the sidebar to navigate:

- **Generate** — paste a transcript, upload a PDF, or enter a ticker.
- **Memo** — view the IC memo produced for a run.
- **Decisions** — log your buy/add/trim/exit decisions.
- **Tracker** — delta reports comparing this quarter to the last.
"""
)

with st.sidebar:
    st.header("Status")
    try:
        from pipeline.config import Config

        Config.load()
        st.success("Config loaded.")
    except Exception as exc:
        st.error(f"Config error: {exc}")
        st.info(
            "Copy `.env.example` to `.env` at the repo root and fill in your "
            "API keys."
        )
