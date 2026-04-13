# Earnings Podcast Agent: Implementation Plan

## Overview

This document breaks the build into concrete tasks with dependencies, acceptance criteria, and the order you should tackle them. Each task is sized to be completable in a single working session (2 to 4 hours). The plan assumes you are building the Claude Artifact version first and adding Streamlit later if needed.

**Total estimated effort:** 19 to 26 days
**Recommended approach:** Build sequentially. Do not skip ahead. Each phase validates the one before it.

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
│   │   ├── msft_q1_2026.txt
│   │   ├── sofi_q4_2025.txt
│   │   ├── tsmc_q1_2026.txt
│   │   ├── duol_q4_2025.txt
│   │   └── nke_q3_2025.txt
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
    │   ├── 1_generate.py
    │   ├── 2_memo.py
    │   ├── 3_decisions.py
    │   └── 4_tracker.py
    └── components/
        ├── audio_player.py
        ├── memo_card.py
        └── decision_form.py
```

---

## Phase 1: Script Pipeline (Days 1 to 5)

This is 60% of the effort. Everything downstream depends on prompt quality here.

### Task 1.1: Project Setup and Anthropic Client

**Time:** 2 hours
**Dependencies:** None

Set up the repository, virtual environment, and a reusable Anthropic API wrapper.

**What to build:**
- Initialize repo with the folder structure above
- Create `requirements.txt` with anthropic, pydub, supabase, python-dotenv
- Build `pipeline/utils/anthropic_client.py` with a wrapper that handles: model selection (Sonnet vs Opus), system prompts, web search tool integration, structured output parsing, retry logic with exponential backoff, token usage logging
- Create `.env.example` with ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY

**Acceptance criteria:**
- Can call Claude Sonnet and Opus from a single function
- Can enable/disable web search per call
- Token usage prints to console for cost tracking
- All API keys loaded from .env

---

### Task 1.2: Step 1 Prompt (Transcript Ingestion)

**Time:** 4 hours
**Dependencies:** Task 1.1

Write and test the prompt that extracts claims and identifies concepts from any earnings transcript.

**What to build:**
- `prompts/step1_transcript_ingestion.md` with the full system prompt
- `pipeline/step1_ingest.py` that accepts raw text and returns structured JSON
- Support for three input modes: raw text, PDF extraction (using pdfplumber), ticker based auto fetch (using web search)

**Prompt must instruct the model to:**
- Extract every material claim with category tags (revenue, margins, growth, guidance, strategic, capex)
- For each claim, list concepts a newcomer would not understand
- Output structured JSON: `{claims: [{text, category, concepts: []}], concept_glossary: [{term, related_claims: []}]}`

**Test against:** MSFT and SOFI transcripts (cloud/SaaS and fintech, very different concept sets)

**Acceptance criteria:**
- Extracts 15+ claims from a megacap transcript
- Identifies 20+ unique concepts
- Concept glossary correctly links terms to their parent claims
- Works for both tech and fintech without prompt changes

---

### Task 1.3: Step 2 Prompt (Business Model Decoder)

**Time:** 4 hours
**Dependencies:** Task 1.2

Write the prompt that builds explanations in dependency order with analogies.

**What to build:**
- `prompts/step2_business_model_decoder.md`
- `pipeline/step2_decode.py` that takes Step 1 output and returns ordered explanations

**Prompt must instruct the model to:**
- Map dependencies between concepts (must understand X before Y)
- Sort explanations in teaching order
- For each concept: plain language definition, why it matters for this company, concrete analogy, which claims it unlocks
- Adapt analogies to the industry automatically

**Test against:** MSFT (cloud metrics), SOFI (bank metrics), TSMC (semiconductor metrics)

**Acceptance criteria:**
- Dependency ordering is logically correct (no forward references)
- Analogies are industry appropriate (no bank analogies for a SaaS company)
- A non finance reader can follow the sequence and understand each concept before it is needed
- 15 to 25 concept explanations per transcript

---

### Task 1.4: Step 3 Prompt (Bearish Critic)

**Time:** 4 hours
**Dependencies:** Task 1.2

Write the prompt for structured skepticism. This step uses Opus for stronger reasoning.

**What to build:**
- `prompts/step3_bearish_critic.md`
- `pipeline/step3_critique.py` that takes claims from Step 1 and produces critiques with web search evidence

**Prompt must apply five lenses per claim:**
1. Metric selection bias
2. Omission detection
3. Assumption testing
4. Historical precedent (requires web search)
5. Counter evidence (requires web search)

**Critical quality bar:** The bear case must be intellectually honest, not contrarian for the sake of it. Each critique needs specific evidence or a named historical parallel.

**Test against:** All five test transcripts

**Acceptance criteria:**
- Produces critiques for 8 to 12 major claims per transcript
- At least 3 critiques per transcript use web search for real data
- Historical parallels cite specific companies and time periods
- Reading the critiques, you sometimes think "the bear might be right"

---

### Task 1.5: Step 4 Prompt (Sector Context)

**Time:** 3 hours
**Dependencies:** Task 1.1

Write the prompt for sector level bull and bear cases.

**What to build:**
- `prompts/step4_sector_context.md`
- `pipeline/step4_sector.py` that identifies the sector from the transcript and builds two opposing narratives

**Prompt must:**
- Auto detect the sector from transcript content
- Build a sector bull case with structural tailwinds
- Build a sector bear case with headwinds
- Use web search for current data on sector trends
- Separate company specific factors from sector wide forces

**Test against:** Cloud (MSFT), fintech (SOFI), semiconductor (TSMC), consumer (NKE)

**Acceptance criteria:**
- Correctly identifies sector without explicit input
- Bull and bear cases reference current data (not stale training knowledge)
- Sector analysis is genuinely different from the company specific analysis

---

### Task 1.6: Step 5 Prompt (Script Generator)

**Time:** 6 hours (longest single task)
**Dependencies:** Tasks 1.2, 1.3, 1.4, 1.5

Write the prompt that synthesizes all upstream output into a 6,500 to 7,500 word three voice script.

**What to build:**
- `prompts/step5_script_generator.md`
- `pipeline/step5_script.py` that takes all upstream outputs and produces the final script

**Prompt must enforce:**
- Seven act structure (Cold Open, Business 101, What Mgmt Said, The Debate, Sector Zoom Out, So What?, Close)
- Three distinct voices with consistent personalities
- HOST interrupts every 3 minutes minimum with "what does that mean?"
- No speaker talks more than 90 seconds without interruption
- Every technical concept gets a concrete example within 30 seconds
- Word count between 6,500 and 7,500
- Speaker tags in format: `HOST:`, `BULL:`, `BEAR:`

**Test against:** All five test transcripts. This is the most iteration intensive step.

**Acceptance criteria:**
- Script reads naturally when read aloud
- All seven acts are present and correctly weighted
- HOST voice is consistently curious, not expert
- BULL and BEAR have genuinely different analytical frameworks
- A non finance listener would understand the business model by end of Act 2
- Word count within target range

---

### Task 1.7: Pipeline Orchestrator

**Time:** 3 hours
**Dependencies:** Tasks 1.2 through 1.6

Wire all five steps into a sequential pipeline.

**What to build:**
- `pipeline/orchestrator.py` with a `run_pipeline(transcript, source_type)` function
- Progress logging (which step is running, time per step, total time)
- Error handling (if a step fails, save partial output and report which step broke)
- Output: all intermediate JSON plus final script saved to a structured dictionary

**Acceptance criteria:**
- Full pipeline runs end to end on all five test transcripts
- Total time under 5 minutes per transcript (excluding audio)
- Partial outputs are accessible if a step fails
- Console shows clear progress: step name, elapsed time, token usage

---

### Task 1.8: Cross Industry Validation

**Time:** 4 hours
**Dependencies:** Task 1.7

Run the full pipeline on all five test transcripts and evaluate quality.

**What to do:**
- Run pipeline on MSFT, SOFI, TSMC, DUOL, NKE
- For each output, evaluate: concept coverage, analogy quality, bear case strength, script readability, voice distinctness
- Document any industry where the pipeline struggles
- Iterate on prompts until quality is consistent across industries

**Acceptance criteria:**
- All five transcripts produce usable podcast scripts
- No industry requires a different prompt (the pipeline is truly company agnostic)
- Quality checklist passes for each output (documented in tests/)

---

## Phase 2: Audio Generation (Days 6 to 8)

### Task 2.1: ElevenLabs Client

**Time:** 3 hours
**Dependencies:** Phase 1 complete

Build the ElevenLabs API wrapper.

**What to build:**
- `pipeline/utils/elevenlabs_client.py` with functions for: text to speech with voice selection, voice parameter configuration (speed, stability), character count estimation before sending, quota checking
- Support for both multilingual_v2 and flash models
- Error handling for rate limits and quota exhaustion

**Acceptance criteria:**
- Can generate speech for a single paragraph with any of the six voices (3 EN, 3 ES)
- Character count estimation matches actual usage within 5%
- Graceful handling when quota is exhausted

---

### Task 2.2: Script Parser and Audio Assembly

**Time:** 4 hours
**Dependencies:** Task 2.1

Parse the script into speaker segments and assemble the final MP3.

**What to build:**
- `pipeline/step6_audio.py` with script parsing and audio generation
- `pipeline/utils/audio_assembler.py` with pydub based concatenation
- Script parser that splits by speaker tags and identifies act boundaries
- Audio assembly: 300ms silence between turns, 800ms between acts
- Progress reporting (X of Y segments complete)

**Acceptance criteria:**
- Parser correctly splits a full script into individual speaker segments
- Audio segments concatenate into a single MP3 without gaps or overlaps
- Silence durations are correct between turns and acts
- Full episode generates in under 5 minutes
- Output MP3 plays correctly in any standard player

---

### Task 2.3: End to End Audio Test

**Time:** 2 hours
**Dependencies:** Task 2.2

Run the full pipeline including audio on one transcript.

**What to do:**
- Pick MSFT transcript
- Run full pipeline: transcript to MP3
- Listen to the full episode
- Note any issues: awkward pauses, mispronunciations, pacing problems, voice confusion
- Adjust voice parameters if needed

**Acceptance criteria:**
- Complete episode plays without technical issues
- Three voices are clearly distinguishable
- Pacing feels natural (not robotic, not rushed)
- Total audio length between 35 and 50 minutes

---

## Phase 3: Spanish Adaptation (Days 9 to 11)

### Task 3.1: Spanish Adaptation Prompt

**Time:** 4 hours
**Dependencies:** Phase 1 complete

Write the prompt that adapts (not translates) the English script for Latin American audiences.

**What to build:**
- `prompts/step5b_spanish_adaptation.md`
- Adaptation logic in `pipeline/step5_script.py`

**Prompt must:**
- Rewrite analogies for Latin American context
- Localize cultural references (Walmart to MercadoLibre, etc.)
- Adjust financial literacy scaffolding
- Maintain the same seven act structure
- Keep the same HOST/BULL/BEAR dynamics with slightly warmer tone

**Acceptance criteria:**
- Spanish script is an adaptation, not a word for word translation
- Analogies reference LatAm companies and contexts
- A Colombian or Mexican listener would find it natural
- Financial concepts get appropriate scaffolding

---

### Task 3.2: Spanish Voice Configuration and Audio

**Time:** 3 hours
**Dependencies:** Tasks 2.2, 3.1

Select Spanish voices and generate the Spanish episode.

**What to build:**
- Spanish voice selection in ElevenLabs (Latin American accent)
- Audio pipeline for Spanish episodes
- Same assembly logic: 300ms turns, 800ms acts

**Acceptance criteria:**
- Three Spanish voices are clearly distinguishable
- Latin American accent sounds natural
- Episode length comparable to English version

---

## Phase 4: Investment Governance (Days 12 to 15)

### Task 4.1: Step 7 Prompt (IC Memo Generator)

**Time:** 4 hours
**Dependencies:** Phase 1 complete

Write the prompt that compresses all analysis into an investment committee memo.

**What to build:**
- `prompts/step7_ic_memo_generator.md`
- `pipeline/step7_memo.py`

**Prompt must produce:**
- Thesis summary (2 sentences max)
- Bull score (1 to 10) with justification
- Bear score (1 to 10) with justification
- Key assumptions (3 to 5) each with 1 to 10 confidence rating, ordered by conviction
- Kill conditions (3 to 5) each with metric name, threshold value, and direction
- Suggested position size as % of portfolio
- Time horizon

**Scoring calibration (must be embedded in prompt):**
- 1 to 2: Weak. Hope based.
- 3 to 4: Below average. Significant gaps.
- 5 to 6: Moderate. Execution dependent.
- 7 to 8: Strong. Well evidenced.
- 9 to 10: Exceptional. Rare. Overwhelming evidence.

**Test against:** All five transcripts

**Acceptance criteria:**
- Scores feel calibrated (a mediocre company does not get an 8, a strong company does not get a 3)
- Kill conditions are specific and measurable (not vague)
- Assumptions are distinct from each other (no overlaps)
- Suggested position size correlates with the bull/bear gap
- Reading the memo, you have enough information to make a decision

---

### Task 4.2: Step 8 (Decision Log) Interface

**Time:** 3 hours
**Dependencies:** Task 4.1

Build the decision logging interface.

**What to build:**
- `pipeline/step8_decision.py` with functions for: creating a decision record, validating required fields, formatting for display
- Input: action, conviction (1 to 10), rationale, price, size
- Validation: action must be one of buy/add/trim/exit/pass/hold, conviction must be 1 to 10, rationale cannot be empty

**Acceptance criteria:**
- Can create a well formed decision record
- Validation catches missing or invalid fields
- Decision links to the IC memo that prompted it

---

### Task 4.3: Step 9 Prompt (Thesis Tracker)

**Time:** 4 hours
**Dependencies:** Task 4.1

Write the prompt that generates delta reports on repeat runs.

**What to build:**
- `prompts/step9_thesis_tracker.md`
- `pipeline/step9_tracker.py`

**Prompt receives:**
- Current quarter's analysis (all upstream output)
- Prior quarter's IC memo (thesis, assumptions, kill conditions)
- Prior quarter's analysis run data

**Prompt must produce:**
- Guidance vs actual comparison: {metric, guided, actual, delta, assessment}
- Assumption status updates: held, weakened, or broken for each
- Kill condition evaluation: any triggered?
- Bull case evolution narrative
- Bear case evolution narrative
- Thesis intact flag (boolean) with explanation
- Recommended action: hold, add, trim, exit, or revisit

**Test approach:** Run pipeline on two consecutive quarters for the same company (e.g., MSFT Q4 2025 and Q1 2026)

**Acceptance criteria:**
- Delta report correctly identifies what changed between quarters
- Assumption status updates are evidence based
- Kill conditions are evaluated against actual data
- Recommended action follows logically from the analysis
- Reading the delta report, you know exactly whether your thesis is on track

---

### Task 4.4: Wire Governance into Orchestrator

**Time:** 2 hours
**Dependencies:** Tasks 4.1, 4.2, 4.3

Add Steps 7 through 9 to the main pipeline.

**What to build:**
- Update `pipeline/orchestrator.py` to run Step 7 after Step 5
- Add logic to detect repeat runs (same company exists in Supabase) and trigger Step 9
- Step 8 is user initiated, not automatic. The orchestrator surfaces the memo and waits for user input.

**Acceptance criteria:**
- First run for a company: Steps 1 through 7 execute, Step 8 waits for user input, Step 9 skips
- Repeat run for a company: Steps 1 through 7 execute, Step 9 generates delta report, Step 8 waits for user input
- All governance outputs are included in the pipeline result dictionary

---

## Phase 5: Supabase Database (Days 16 to 18)

### Task 5.1: Database Schema and Migrations

**Time:** 4 hours
**Dependencies:** None (can be done in parallel with earlier phases)

Create the Supabase tables including the RAG ready analysis_chunks table.

**What to build:**
- All nine migration files in `supabase/migrations/`
- RLS policies scoped to authenticated user
- Indexes on: `companies.ticker`, `analysis_runs.company_id`, `analysis_runs.quarter`, `decisions.company_id`, `kill_conditions.status`, `analysis_chunks.company_id`, `analysis_chunks.chunk_type`, `analysis_chunks.run_id`
- pgvector extension enabled (for future RAG use)

**Migration 001: companies**
```sql
create table companies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  ticker text not null,
  name text not null,
  sector text,
  first_analyzed_at timestamptz default now(),
  notes text,
  unique(user_id, ticker)
);
```

**Migration 002: analysis_runs**
```sql
create table analysis_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  company_id uuid references companies(id) not null,
  quarter text not null,
  run_date timestamptz default now(),
  transcript_source text not null,
  claims_json jsonb,
  concepts_json jsonb,
  explanations_json jsonb,
  critiques_json jsonb,
  sector_context_json jsonb,
  script_en text,
  script_es text,
  audio_en_url text,
  audio_es_url text,
  status text not null default 'running',
  duration_seconds integer
);
```

**Migration 003: ic_memos**
```sql
create table ic_memos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  run_id uuid references analysis_runs(id) not null,
  company_id uuid references companies(id) not null,
  thesis_summary text not null,
  bull_score integer not null check (bull_score between 1 and 10),
  bear_score integer not null check (bear_score between 1 and 10),
  key_assumptions jsonb not null,
  suggested_size_pct numeric,
  time_horizon text,
  memo_text text not null,
  created_at timestamptz default now()
);
```

**Migration 004: decisions**
```sql
create table decisions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  company_id uuid references companies(id) not null,
  memo_id uuid references ic_memos(id),
  decision_date date not null default current_date,
  action text not null check (action in ('buy','add','trim','exit','pass','hold')),
  size_pct numeric,
  price_at_decision numeric,
  rationale text not null,
  conviction integer not null check (conviction between 1 and 10),
  created_at timestamptz default now()
);
```

**Migration 005: kill_conditions**
```sql
create table kill_conditions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  memo_id uuid references ic_memos(id) not null,
  company_id uuid references companies(id) not null,
  condition_text text not null,
  metric_name text,
  threshold_value numeric,
  threshold_direction text check (threshold_direction in ('below','above')),
  status text not null default 'active' check (status in ('active','triggered','cleared','retired')),
  triggered_at timestamptz,
  triggered_by_run_id uuid references analysis_runs(id),
  notes text,
  created_at timestamptz default now()
);
```

**Migration 006: thesis_reviews**
```sql
create table thesis_reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  current_run_id uuid references analysis_runs(id) not null,
  prior_run_id uuid references analysis_runs(id) not null,
  company_id uuid references companies(id) not null,
  guidance_vs_actual jsonb,
  assumptions_status jsonb,
  kill_conditions_status jsonb,
  bear_case_evolution text,
  bull_case_evolution text,
  thesis_still_intact boolean not null,
  recommended_action text not null,
  review_text text not null,
  created_at timestamptz default now()
);
```

**Migration 007: analysis_chunks (RAG ready)**
```sql
create table analysis_chunks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  run_id uuid references analysis_runs(id) not null,
  company_id uuid references companies(id) not null,
  chunk_type text not null check (chunk_type in (
    'claim', 'concept', 'critique', 'sector_bull', 'sector_bear',
    'assumption', 'kill_condition', 'thesis_summary', 'delta_observation'
  )),
  chunk_text text not null,
  metadata jsonb not null default '{}',
  embedding vector(1536),  -- null until RAG is enabled
  created_at timestamptz default now()
);

create index idx_chunks_company on analysis_chunks(company_id);
create index idx_chunks_run on analysis_chunks(run_id);
create index idx_chunks_type on analysis_chunks(chunk_type);
```

**Migration 008: RLS policies**
```sql
-- Enable RLS on all tables
alter table companies enable row level security;
alter table analysis_runs enable row level security;
alter table ic_memos enable row level security;
alter table decisions enable row level security;
alter table kill_conditions enable row level security;
alter table thesis_reviews enable row level security;
alter table analysis_chunks enable row level security;

-- Each table gets the same policy pattern
-- Example for companies (repeat for all tables):
create policy "Users can view own data" on companies
  for select using (auth.uid() = user_id);
create policy "Users can insert own data" on companies
  for insert with check (auth.uid() = user_id);
create policy "Users can update own data" on companies
  for update using (auth.uid() = user_id);
```

**Migration 009: pgvector extension**
```sql
-- Enable pgvector for future RAG use
-- Embedding column already exists on analysis_chunks (nullable)
-- This migration just enables the extension
create extension if not exists vector;

-- Index will be created when RAG is enabled and embeddings are populated
-- create index idx_chunks_embedding on analysis_chunks
--   using ivfflat (embedding vector_cosine_ops) with (lists = 100);
```

**Acceptance criteria:**
- All seven tables created with correct constraints
- Check constraints enforce 1 to 10 scoring on bull_score, bear_score, conviction
- Check constraints enforce valid action values and chunk types
- RLS policies prevent cross user data access on all seven tables
- Foreign keys maintain referential integrity
- pgvector extension enabled
- analysis_chunks embedding column accepts null (no embeddings required yet)

---

### Task 5.2: Chunker Utility

**Time:** 3 hours
**Dependencies:** Task 5.1, Phase 1 complete

Build the utility that decomposes each pipeline step's output into individually addressable chunks with standardized metadata.

**What to build:**
- `pipeline/utils/chunker.py` with functions for:
  - `chunk_claims(claims_json, ticker, quarter)` : one chunk per claim, metadata includes category tag
  - `chunk_concepts(concepts_json, ticker, quarter)` : one chunk per concept, metadata includes related_claim_ids
  - `chunk_critiques(critiques_json, ticker, quarter)` : one chunk per critique, metadata includes lens type and target claim
  - `chunk_sector_context(sector_json, ticker, quarter)` : two chunks (sector_bull, sector_bear)
  - `chunk_memo(memo_data, ticker, quarter)` : thesis_summary chunk plus one chunk per assumption plus one chunk per kill condition, metadata includes scores
  - `chunk_delta_report(review_data, ticker, quarter)` : one chunk per significant observation from the delta report
  - `build_metadata(ticker, quarter, chunk_type, **extras)` : standardized metadata envelope builder

**Each chunk is a dictionary:**
```python
{
    "chunk_type": "critique",
    "chunk_text": "Management highlighted 35% ARR growth but switched from
                   net to gross revenue recognition this quarter...",
    "metadata": {
        "ticker": "CRM",
        "quarter": "Q1_2026",
        "category": "revenue",
        "lens": "metric_selection",
        "target_claim_id": "claim_003"
    }
}
```

**Quality rules:**
- Each chunk contains exactly one coherent idea (50 to 200 words)
- No chunk duplicates information from another chunk in the same run
- Metadata always includes ticker, quarter, and chunk_type at minimum
- Chunks are deterministic: same input always produces same chunks

**Test with:** Run chunker on all five test transcript pipeline outputs. Verify chunk counts, text lengths, and metadata completeness.

**Acceptance criteria:**
- One pipeline run produces 60 to 80 chunks
- Every chunk has complete metadata
- No chunk exceeds 250 words
- No chunk is shorter than 20 words
- Chunk types match the allowed values in the database check constraint

---

### Task 5.3: Supabase Client and Pipeline Integration

**Time:** 4 hours
**Dependencies:** Tasks 5.1, 5.2, 4.4

Wire Supabase and the chunker into the pipeline.

**What to build:**
- `pipeline/utils/supabase_client.py` with functions for:
  - `get_or_create_company(ticker, name, sector)` : upsert logic
  - `save_analysis_run(company_id, quarter, data)` : insert with all jsonb fields
  - `save_ic_memo(run_id, company_id, memo_data)` : insert memo with scores
  - `save_decision(company_id, memo_id, decision_data)` : append only insert
  - `save_kill_conditions(memo_id, company_id, conditions)` : batch insert
  - `save_chunks(run_id, company_id, chunks)` : batch insert all chunks for a run
  - `get_prior_run(company_id)` : fetch most recent completed run
  - `get_active_kill_conditions(company_id)` : fetch for thesis tracker
  - `update_kill_condition_status(id, status, triggered_by_run_id)` : status change
  - `save_thesis_review(review_data)` : insert delta report
- Update orchestrator to call chunker after each step and batch insert chunks at end of run
- Chunking happens inline during pipeline execution, not as a post processing step

**Chunk writing flow in orchestrator:**
```python
chunks = []

# After Step 1
chunks.extend(chunker.chunk_claims(claims, ticker, quarter))
chunks.extend(chunker.chunk_concepts(concepts, ticker, quarter))

# After Step 3
chunks.extend(chunker.chunk_critiques(critiques, ticker, quarter))

# After Step 4
chunks.extend(chunker.chunk_sector_context(sector, ticker, quarter))

# After Step 7
chunks.extend(chunker.chunk_memo(memo, ticker, quarter))

# After Step 9 (if repeat run)
chunks.extend(chunker.chunk_delta_report(review, ticker, quarter))

# Single batch insert at end
supabase.save_chunks(run_id, company_id, chunks)
```

**Acceptance criteria:**
- Full pipeline run persists all data to Supabase including 60 to 80 chunks
- Second run for the same company correctly retrieves prior data
- Kill condition status updates work
- Chunks are written in a single batch insert (not one at a time)
- No data loss on pipeline failure (partial results saved, chunks batch may be lost on late failure which is acceptable since they can be regenerated from the jsonb blobs)
- Embedding column is null on all chunks (populated later when RAG is enabled)

---

## Phase 6: User Interface (Days 19 to 22)

### Task 6.1: Claude Artifact (React)

**Time:** 6 hours
**Dependencies:** Phases 1 through 5

Build the single file React artifact that runs inside Claude.

**What to build:**
- `artifact/earnings_podcast.jsx` containing:
  - Transcript input (paste, upload, ticker)
  - Pipeline progress indicator
  - Script viewer with speaker color coding
  - Audio player (HTML5) with play/pause/seek
  - IC Memo display card with scores visualized
  - Decision form (action, conviction 1 to 10, rationale, price, size)
  - Thesis tracker delta report view (on repeat runs)
  - Kill conditions dashboard with status indicators

**UI sections:**
1. Input panel: paste area, file upload, ticker search
2. Progress bar: steps 1 through 9 with time estimates
3. Podcast tab: script text + audio player + download
4. Governance tab: IC memo + decision form + kill conditions
5. History tab: prior runs for this company + delta reports

**Acceptance criteria:**
- All functionality works in a single .jsx file
- Supabase client SDK connects directly from the artifact
- Audio plays inline
- Decision form validates inputs before submission
- Prior run data loads correctly for repeat analyses

---

### Task 6.2: Streamlit App (Alternative)

**Time:** 6 hours
**Dependencies:** Phases 1 through 5

Build the Streamlit version for standalone deployment. Only build this after validating the artifact version.

**What to build:**
- `streamlit/app.py` main entry point
- Four pages: Generate, Memo, Decisions, Tracker
- Server side Supabase client (no exposed keys)
- st.audio for playback, st.download_button for MP3 export

**Acceptance criteria:**
- All pipeline steps run from the Streamlit interface
- Audio plays and downloads correctly
- Governance views mirror the artifact functionality
- Deployable to Streamlit Cloud or Railway

---

## Phase 7: Polish (Days 23 to 26)

### Task 7.1: Prompt Tuning Across Industries

**Time:** 4 hours
**Dependencies:** All phases complete

Run the full pipeline on 10+ companies across different industries and fix any quality issues.

**Test companies:**
- Cloud/SaaS: MSFT, CRM
- Fintech: SOFI, NU
- Semiconductor: TSMC, NVDA
- Consumer: NKE, SBUX
- Pharma: LLY, ABBV
- Energy: XOM

**What to look for:**
- Concept coverage gaps (industry specific terms missed)
- Analogy quality (forced or awkward analogies)
- Bear case strength (too weak or too aggressive)
- Script pacing (any acts too long or too short)
- Memo scoring calibration (scores match evidence quality)
- Kill condition specificity (concrete enough to monitor)

---

### Task 7.2: Voice Fine Tuning

**Time:** 3 hours
**Dependencies:** Phase 2 complete

Listen to full episodes and adjust voice parameters.

**What to tune:**
- Speed per voice (does the bear sound deliberate enough?)
- Stability (is the bull expressive without being chaotic?)
- Silence durations (do turn transitions feel natural?)
- Act transitions (is the 800ms gap right?)

---

### Task 7.3: Edge Cases

**Time:** 3 hours
**Dependencies:** All phases

Test and handle failure modes.

**Edge cases to cover:**
- Very short transcript (15 min earnings call)
- Very long transcript (90 min call with extended Q&A)
- Transcript in poor format (OCR artifacts, missing sections)
- Company with no prior web data (small cap, limited coverage)
- Ticker not found (invalid input)
- ElevenLabs quota exhausted mid episode
- Supabase connection failure
- LLM returns malformed JSON

---

### Task 7.4: Documentation

**Time:** 2 hours
**Dependencies:** All phases

Write the README and finalize documentation.

**What to write:**
- README.md: project overview, setup instructions, usage guide, examples
- .env.example with all required variables
- Prompt files include version numbers and change notes
- CHANGELOG.md for tracking prompt iterations

---

## Milestone Checklist

| Milestone | Phase | What It Proves |
|-----------|-------|---------------|
| First working script from transcript | Phase 1 | Core pipeline works |
| Scripts work across 5 industries | Phase 1 | Pipeline is company agnostic |
| First complete audio episode | Phase 2 | Full podcast pipeline works |
| First Spanish episode | Phase 3 | Bilingual pipeline works |
| First IC memo with 1/10 scores | Phase 4 | Governance layer works |
| First thesis delta report | Phase 4 | Feedback loop closes |
| All data persists in Supabase including chunks | Phase 5 | Persistence layer works with RAG ready decomposition |
| Chunk counts match expected range (60 to 80 per run) | Phase 5 | Chunker produces correct output |
| Full UI with playback and governance | Phase 6 | User experience is complete |
| Works across 10+ companies | Phase 7 | Production ready |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Script quality inconsistent across industries | High | Extensive prompt iteration in Phase 1. Budget extra days here. |
| ElevenLabs voices sound robotic | Medium | Test multiple voice options early. Flash model may sound different from multilingual_v2. |
| Scoring calibration is off (everything gets 7/10) | Medium | Embed detailed calibration guide in prompt. Test across strong and weak companies. |
| Kill conditions too vague to monitor | Medium | Add validation in prompt: each condition must have a metric name, threshold, and direction. |
| Supabase free tier limits hit | Low | 500MB is generous for text data. Audio stored externally. 80 chunks per run at ~150 words each is ~60KB per run. 100 runs = 6MB. |
| Pipeline takes too long (>10 min) | Medium | Step 3 (Opus) is the bottleneck. Consider Sonnet for critique if Opus is too slow. |
| Chunk quality degrades RAG retrieval | Medium | Enforce 50 to 200 word range per chunk. One idea per chunk. Test retrieval quality before enabling RAG. |
| Embedding costs add up at scale | Low | Only embed when RAG is enabled. ~80 chunks per run at ~$0.0001 per embedding = $0.008 per run. Negligible. |

---

## Future: RAG Enablement (When Ready)

This is not part of the initial build. Execute this after you have at least 3 companies with 2+ quarters of data each and you find yourself wanting to query across analyses.

### Task R.1: Backfill Embeddings

**Time:** 2 hours
**Dependencies:** Phase 5 complete, sufficient data accumulated

**What to build:**
- `rag/embeddings.py` with a function that takes chunk text and returns a vector(1536) using an embedding model
- `rag/backfill.py` that queries all analysis_chunks where embedding is null and populates them in batches of 100
- Add embedding generation to the pipeline orchestrator so new chunks get embedded at write time

**Acceptance criteria:**
- All existing chunks have embeddings populated
- New pipeline runs generate embeddings inline
- Batch backfill completes without timeouts

---

### Task R.2: Query Router

**Time:** 3 hours
**Dependencies:** Task R.1

**What to build:**
- `rag/query_router.py` with:
  - `classify_query(question)` : determines if the question is structured (SQL) or semantic (vector search) or hybrid (both)
  - `structured_query(question)` : translates to SQL against ic_memos, decisions, kill_conditions
  - `semantic_query(question, filters)` : runs pgvector similarity search on analysis_chunks with optional WHERE clause on ticker, quarter, chunk_type
  - `hybrid_query(question, filters)` : SQL filter then vector similarity on filtered subset
  - `answer(question, results)` : passes retrieved chunks plus question to Claude for synthesis

**Query patterns:**
- "Which holdings have the weakest assumptions?" → structured (SQL on key_assumptions scores)
- "What margin risks are showing up across my portfolio?" → semantic (vector search on chunk_type = critique, all tickers)
- "Find critiques from the last two quarters similar to deposit cost pressure" → hybrid (SQL filter on quarter and chunk_type, then vector similarity)

**Acceptance criteria:**
- Structured queries return correct results from SQL
- Semantic queries return relevant chunks ranked by similarity
- Hybrid queries correctly combine filtering and similarity
- End to end: question in, synthesized answer out

---

### Task R.3: Create IVFFlat Index

**Time:** 30 minutes
**Dependencies:** Task R.1 (need populated embeddings to build index)

```sql
-- Only run after embeddings are populated
-- lists value should be roughly sqrt(total_chunks)
create index idx_chunks_embedding on analysis_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
```

This index makes similarity search fast. Without it, pgvector does a sequential scan which is fine for <10K chunks but slows down beyond that. At 80 chunks per run and 4 runs per quarter across 10 companies, you hit 10K chunks after roughly 30 quarters. Build the index early, it costs nothing.

---

## Environment Variables

```
# Required
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Optional
ELEVENLABS_MODEL=eleven_multilingual_v2   # or eleven_flash_v2_5
DEFAULT_HOST_VOICE=Rachel
DEFAULT_BULL_VOICE=Antoni
DEFAULT_BEAR_VOICE=Clyde

# RAG (only needed when RAG is enabled)
# EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_API_KEY=sk-...  # if using OpenAI embeddings
```

---

## Quick Start (After Setup)

```bash
# Clone and install
git clone https://github.com/your-username/earnings-podcast-agent.git
cd earnings-podcast-agent
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env

# Run Supabase migrations
supabase db push

# Generate a podcast
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026

# Generate with audio
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026 --audio

# Generate bilingual
python -m pipeline.orchestrator --ticker MSFT --quarter Q1_2026 --audio --spanish
```
