# Earnings Podcast Agent

Turn any company's earnings call into a 45 minute educational podcast with built in investment governance.

Three AI voices debate the company: a curious Host, a data driven Bull analyst, and a skeptical Bear analyst. The listener walks away understanding the business model, the key claims, and the risks, regardless of prior knowledge.

Works for any company in any industry. Microsoft, SoFi, TSMC, Nike, Duolingo, whatever you throw at it.

---

## What It Does

**Podcast Pipeline (Steps 1 to 6)**

Paste a transcript, upload a PDF, or enter a ticker. The pipeline extracts every material claim, identifies every concept a newcomer would need explained, builds explanations in dependency order with concrete analogies, generates structured counter arguments using web search, researches sector level bull and bear cases, and writes a 6,500 to 7,500 word three voice script. Optionally generates a 45 minute MP3 via ElevenLabs. Supports English and Spanish (adaptation, not translation).

**Investment Governance (Steps 7 to 9)**

Compresses the analysis into an IC Memo with 1 to 10 scored bull/bear cases, ranked assumptions, and measurable kill conditions. Logs every decision (buy, pass, add, trim, exit) with conviction scores and rationale. On repeat runs for the same company, generates a delta report comparing guidance vs actual results, tracking assumption status, and checking kill conditions.

**RAG Ready**

Every pipeline run decomposes its output into 60 to 80 individually addressable chunks stored in Supabase with a nullable embedding column. When you have enough data, enable pgvector and query across your entire analysis history: "which of my holdings faces similar margin pressure?" or "are any of my bull theses contradicting each other?"

---

## Stack

| Component | Technology |
|-----------|-----------|
| Orchestration | Python |
| LLM | Claude Sonnet 4 + Claude Opus 4 (for critique) |
| Web Search | Claude API web_search tool |
| Audio | ElevenLabs multilingual_v2 |
| Database | Supabase (PostgreSQL + pgvector) |
| UI | Claude Artifact (React) or Streamlit |

---

## Quick Start

```bash
git clone https://github.com/your-username/earnings-podcast-agent.git
cd earnings-podcast-agent
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys

# Run Supabase migrations
supabase db push

# Generate a podcast
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026

# Generate with audio
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026 --audio

# Generate bilingual
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026 --audio --spanish
```

---

## Environment Variables

```
# Required
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Optional
ELEVENLABS_MODEL=eleven_multilingual_v2
DEFAULT_HOST_VOICE=Rachel
DEFAULT_BULL_VOICE=Antoni
DEFAULT_BEAR_VOICE=Clyde

# RAG (only when enabled)
# EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_API_KEY=sk-...
```

---

## Repository Structure

```
earnings-podcast-agent/
├── README.md
├── TECHNICAL_BRIEF.md
├── IMPLEMENTATION_PLAN.md
├── .env.example
├── .gitignore
├── requirements.txt
├── supabase/
│   ├── migrations/
│   │   ├── 001_create_companies.sql
│   │   ├── 002_create_analysis_runs.sql
│   │   ├── 003_create_ic_memos.sql
│   │   ├── 004_create_decisions.sql
│   │   ├── 005_create_kill_conditions.sql
│   │   ├── 006_create_thesis_reviews.sql
│   │   ├── 007_create_analysis_chunks.sql
│   │   ├── 008_create_rls_policies.sql
│   │   └── 009_enable_pgvector.sql
│   └── seed.sql
├── prompts/
│   ├── step1_transcript_ingestion.md
│   ├── step2_business_model_decoder.md
│   ├── step3_bearish_critic.md
│   ├── step4_sector_context.md
│   ├── step5_script_generator.md
│   ├── step5b_spanish_adaptation.md
│   ├── step7_ic_memo_generator.md
│   └── step9_thesis_tracker.md
├── pipeline/
│   ├── __init__.py
│   ├── config.py
│   ├── orchestrator.py
│   ├── step1_ingest.py
│   ├── step2_decode.py
│   ├── step3_critique.py
│   ├── step4_sector.py
│   ├── step5_script.py
│   ├── step6_audio.py
│   ├── step7_memo.py
│   ├── step8_decision.py
│   ├── step9_tracker.py
│   └── utils/
│       ├── anthropic_client.py
│       ├── elevenlabs_client.py
│       ├── supabase_client.py
│       ├── chunker.py
│       └── audio_assembler.py
├── rag/
│   ├── __init__.py
│   ├── embeddings.py
│   ├── query_router.py
│   └── backfill.py
├── tests/
│   ├── transcripts/
│   ├── test_step1.py
│   ├── test_step2.py
│   ├── test_step3.py
│   ├── test_step5.py
│   ├── test_step7.py
│   ├── test_step9.py
│   ├── test_chunker.py
│   └── test_full_pipeline.py
├── artifact/
│   └── earnings_podcast.jsx
└── streamlit/
    ├── app.py
    ├── pages/
    └── components/
```

---

## How the Pipeline Works

```
Transcript (paste, upload, or ticker)
    |
    v
[1. Transcript Ingestion] ---------> claims + concepts
    |
    v
[2. Business Model Decoder] -------> explanations (ordered)
    |
    v
[3. Bearish Critic] ---------------> critiques + evidence
    |
    v
[4. Sector Context] ---------------> sector bull + bear
    |
    v
[5. Script Generator] -------------> podcast script (7K words)
    |         |
    v         v
[6. EN Audio] [5b. Spanish] -------> english.mp3 + spanish.mp3

    === GOVERNANCE LAYER ===

[7. IC Memo Generator] ------------> structured memo + 1/10 scores
    |
    v
[8. Decision Log] -----------------> Supabase (append only)
    |
    v
[9. Thesis Tracker] ---------------> delta report (on repeat runs)
```

Total pipeline time: 5 to 8 minutes. ElevenLabs audio is the bottleneck.

---

## Database Schema

Seven tables in Supabase with row level security:

| Table | Purpose |
|-------|---------|
| companies | One row per ticker |
| analysis_runs | One row per pipeline execution, stores all intermediate jsonb outputs |
| ic_memos | Investment committee memo with 1 to 10 bull/bear scores |
| decisions | Append only log of every investment decision |
| kill_conditions | Measurable conditions that would invalidate a thesis |
| thesis_reviews | Delta reports comparing current vs prior quarter analysis |
| analysis_chunks | RAG ready decomposition: 60 to 80 chunks per run with nullable embeddings |

Full schema details in [TECHNICAL_BRIEF.md](TECHNICAL_BRIEF.md).

---

## Cost

| Setup | Cost |
|-------|------|
| Claude Artifact version | $0 extra (covered by existing Claude + ElevenLabs subscriptions) |
| Supabase | $0 (free tier: 500MB DB, pgvector included) |
| Standalone Streamlit version | $1.90 to $3.30 per episode in API costs |

ElevenLabs Creator plan ($22/mo) supports 1 bilingual episode per month. Pro ($99/mo) supports 7.

---

## Development Timeline

| Phase | Days |
|-------|------|
| 1. Script Pipeline (Steps 1 to 5) | 4 to 5 |
| 2. Audio Generation | 2 to 3 |
| 3. Spanish Adaptation | 2 to 3 |
| 4. Investment Governance (Steps 7 to 9) | 3 to 4 |
| 5. Supabase + Chunker | 2 to 3 |
| 6. UI | 3 to 4 |
| 7. Polish | 3 to 4 |
| **Total** | **19 to 26** |

Phase 1 is 60% of the effort. Prompt quality determines everything downstream.

---

## Documentation

| Document | What It Covers |
|----------|---------------|
| [TECHNICAL_BRIEF.md](TECHNICAL_BRIEF.md) | Full product spec: pipeline steps, prompt design, voice configuration, script structure, governance layer, database schema, RAG architecture, cost analysis |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Task by task build plan with dependencies, acceptance criteria, SQL migrations, code snippets, risk register, and RAG enablement roadmap |

---

## License

MIT
