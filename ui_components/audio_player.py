"""Audio player component — thin wrapper so callers don't import streamlit."""

from __future__ import annotations

import streamlit as st


def render_audio(path: str, label: str = "Audio") -> None:
    st.subheader(label)
    st.audio(path)
    with open(path, "rb") as fh:
        st.download_button("Download MP3", data=fh, file_name=path.split("/")[-1])
