"""Generate page — run the pipeline and persist the result."""

from __future__ import annotations

from ui_components.secrets_bridge import push_secrets_to_env

push_secrets_to_env()

import time  # noqa: E402
from pathlib import Path  # noqa: E402

import streamlit as st  # noqa: E402

from pipeline.orchestrator import run_pipeline  # noqa: E402
from pipeline.utils.supabase_client import SupabasePipelineClient  # noqa: E402

st.title("Generate")

mode = st.radio("Input mode", ["Paste transcript", "Upload PDF", "Ticker"], horizontal=True)

ticker = st.text_input("Ticker", value="MSFT").strip().upper()
quarter = st.text_input("Quarter tag (e.g. Q1_2026)", value="Q1_2026").strip()
company_name = st.text_input("Company name (for DB, optional)", value="")

source: str | None = None
source_type: str | None = None

if mode == "Paste transcript":
    source = st.text_area("Paste the full earnings-call transcript", height=300)
    source_type = "text"
elif mode == "Upload PDF":
    pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if pdf:
        tmp = Path("out") / f"{ticker}_{quarter}.pdf"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(pdf.getvalue())
        source = str(tmp)
        source_type = "pdf"
else:
    source = ticker
    source_type = "ticker"

with st.expander("Options"):
    audio = st.checkbox("Generate audio (ElevenLabs)", value=False)
    spanish = st.checkbox("Also produce Spanish version", value=False)
    persist = st.checkbox("Persist to Supabase", value=True)

run = st.button("Run pipeline", type="primary", disabled=not source)

if run and source and source_type:
    with st.status("Running pipeline…", expanded=True) as status:
        start = time.monotonic()
        try:
            result = run_pipeline(
                source=source,
                source_type=source_type,
                ticker=ticker,
                quarter=quarter,
                audio=audio,
                spanish=spanish,
            )
        except Exception as exc:
            status.update(label=f"Pipeline failed: {exc}", state="error")
            st.stop()

        elapsed = time.monotonic() - start
        status.update(label=f"Pipeline complete in {elapsed:.0f}s", state="complete")

    st.subheader("Summary")
    cols = st.columns(4)
    cols[0].metric("Claims", len((result.step1 or {}).get("claims", [])))
    cols[1].metric("Critiques", len((result.step3 or {}).get("critiques", [])))
    cols[2].metric("Chunks", len(result.chunks))
    cols[3].metric("Bull / Bear",
                   f'{(result.memo or {}).get("bull_score","?")} / {(result.memo or {}).get("bear_score","?")}')

    tabs = st.tabs(["Script", "IC memo", "Critiques", "Chunks"])
    with tabs[0]:
        if result.script_en:
            st.download_button("Download EN script",
                               data=result.script_en,
                               file_name=f"{ticker}_{quarter}_en.txt")
            st.markdown(f"```\n{result.script_en[:4000]}\n```")
        if result.script_es:
            st.download_button("Download ES script",
                               data=result.script_es,
                               file_name=f"{ticker}_{quarter}_es.txt")
        if result.audio_en_path and Path(result.audio_en_path).exists():
            st.audio(result.audio_en_path)
    with tabs[1]:
        st.json(result.memo or {})
    with tabs[2]:
        st.json(result.step3 or {})
    with tabs[3]:
        st.write(f"{len(result.chunks)} chunks generated.")
        st.json(result.chunks[:5])

    if persist:
        with st.status("Persisting to Supabase…", expanded=False) as status:
            try:
                sb = SupabasePipelineClient()
                company = sb.get_or_create_company(ticker, company_name or ticker)
                run_row = sb.save_analysis_run(
                    company_id=company["id"],
                    quarter=quarter,
                    transcript_source=source_type,
                    claims=result.step1,
                    explanations=result.step2,
                    critiques=result.step3,
                    sector_context=result.step4,
                    script_en=result.script_en,
                    script_es=result.script_es,
                    prompt_versions=result.prompt_versions,
                    model_versions=result.model_versions,
                    status="complete",
                    duration_seconds=int(elapsed),
                )
                if result.memo:
                    memo_row = sb.save_ic_memo(run_row["id"], company["id"], result.memo)
                    sb.save_kill_conditions(
                        memo_row["id"],
                        company["id"],
                        result.memo.get("kill_conditions", []),
                    )
                if result.chunks:
                    sb.save_chunks(run_row["id"], company["id"], result.chunks)
                status.update(label="Persisted.", state="complete")
                st.session_state["last_run_id"] = run_row["id"]
                st.session_state["last_company_id"] = company["id"]
                st.session_state["last_memo"] = result.memo
            except Exception as exc:
                status.update(label=f"Persistence failed: {exc}", state="error")
