"""Earnings Podcast Agent — Streamlit entry point.

Run with::

    streamlit run streamlit/app.py

Secrets are read from ``st.secrets`` (``.streamlit/secrets.toml`` locally
or the Secrets tab on Streamlit Community Cloud) and pushed into
``os.environ`` so the pipeline's ``Config`` picks them up unchanged.

The home page explains the product; individual workflows live on the
numbered pages in ``streamlit/pages/``.
"""

from __future__ import annotations

from ui_components.secrets_bridge import push_secrets_to_env

push_secrets_to_env()

import streamlit as st  # noqa: E402  (must come after the secrets bridge)

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
            "Set your API keys in Streamlit secrets "
            "(`.streamlit/secrets.toml` locally, or the Secrets tab on "
            "Streamlit Community Cloud). See "
            "`.streamlit/secrets.toml.example` for the full list of keys."
        )
