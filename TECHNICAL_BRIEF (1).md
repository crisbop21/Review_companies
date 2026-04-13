# Earnings Podcast Agent

## Technical Implementation Brief

**Turn any company's earnings call into a 45 minute educational podcast**

Three voices: Host + Bull Analyst + Bear Analyst
Languages: English + Spanish (separate episodes)
Stack: Claude API + ElevenLabs + Supabase + Claude Artifact or Streamlit
Cost: $0 extra beyond existing subscriptions

**NEW IN V5:** Investment Governance Layer
IC Memo Generator + Decision Log + Thesis Tracker + Supabase persistence

Version 5.0 | April 2026

---

## Table of Contents

1. Product Vision
2. How It Works (9 Step Pipeline)
3. Architecture
4. Step 1: Transcript Ingestion
5. Step 2: Business Model Decoder
6. Step 3: Bearish Critic
7. Step 4: Sector Context Research
8. Step 5: Podcast Script Generator
9. Step 6: Audio Generation (ElevenLabs)
10. Voice Configuration
11. Script Structure and Pacing
12. Spanish Episode Adaptation
13. Example Script Fragments
14. **NEW: Step 7: IC Memo Generator**
15. **NEW: Step 8: Decision Log**
16. **NEW: Step 9: Thesis Tracker**
17. **NEW: Supabase Database Schema**
18. **NEW: RAG Ready: Analysis Chunks**
19. Technology Stack
20. Cost Analysis
21. Development Phases
22. Build Options: Claude Artifact vs Streamlit

---

## 1. Product Vision

Most people cannot sit through an earnings call. Even investors who read the transcript miss the context that makes the numbers meaningful. They hear management claim things like "our annualized run rate crossed $X billion" or "we expect margin expansion in the back half" without understanding what those claims actually mean, whether they are fairly presented, or what management is not saying.

This tool takes any company's earnings call transcript and produces a 40 to 50 minute podcast episode where three voices debate the company. The host asks the questions a smart newcomer would ask. The bull analyst makes the strongest possible case. The bear analyst tears it apart. By the end, the listener genuinely understands the business model, the industry dynamics, and the risks, regardless of prior knowledge.

The tool is company agnostic. It works for a megacap like Microsoft, a mid cap like Duolingo, a fintech like SoFi, a semiconductor company like TSMC, or a consumer brand like Nike. The pipeline adapts its explanations, analogies, and sector context to whatever company is analyzed.

### Target Listener

Someone smart and curious about investing who does not have a finance background or deep knowledge of the specific company. They want to understand the business, not just the numbers. They want both sides of the argument. They want to form their own opinion.

### What Makes This Different

Existing AI podcast tools summarize content. This tool teaches content. A summary assumes you already understand the concepts. This tool assumes you do not, identifies every concept that needs explaining, builds explanations in dependency order, and weaves them into a natural debate.

### V5: From Education to Decision Process

Version 5 adds an investment governance layer inspired by how hedge funds analyze and make decisions on stocks. The podcast pipeline (Steps 1 through 6) remains unchanged. Three new steps transform the output from educational content into a structured investment process: an IC Memo Generator that compresses analysis into a decision ready format, a Decision Log that creates accountability over time, and a Thesis Tracker that closes the feedback loop by comparing each new quarter's results against prior assumptions. All data persists in Supabase.

---

## 2. How It Works (9 Step Pipeline)

| Step | What Happens | Output | Time |
|------|-------------|--------|------|
| 1. Transcript Ingestion | User provides earnings call (paste text, upload PDF, or enter ticker to auto fetch). LLM extracts claims AND identifies every concept requiring explanation. | Claims list + concept glossary | 15 to 20 sec |
| 2. Business Model Decoder | For each concept, builds an explanation from first principles. Maps dependencies. Generates analogies. Adapts to any industry. | Ordered explanation sequence | 30 to 45 sec |
| 3. Bearish Critic | For each major claim, searches for counter evidence, identifies omissions, finds historical parallels. Uses web search for current data. | Critique per claim with evidence | 45 to 90 sec |
| 4. Sector Context | Researches bull and bear cases for the entire industry. Macro forces, competitive dynamics, regulatory trends. | Sector bull thesis + sector bear thesis | 30 to 45 sec |
| 5. Script Generator | Takes all upstream output and writes a 6,500 to 7,500 word three voice podcast script with natural debate flow. | Full script with HOST/BULL/BEAR tags | 60 to 90 sec |
| 6. Audio Generation | Sends script segments to ElevenLabs API with three distinct voices. Concatenates into single MP3. | 45 min MP3 podcast episode | 3 to 5 min |
| **7. IC Memo Generator (NEW)** | Compresses all upstream analysis into a structured one pager: thesis, assumptions ranked by conviction, kill conditions, suggested position size. | IC memo with 1/10 scores | 15 to 30 sec |
| **8. Decision Log (NEW)** | User records action taken (buy, pass, add, trim, exit) with rationale and conviction score. Persisted to Supabase. | Append only decision record | Manual input |
| **9. Thesis Tracker (NEW)** | On subsequent runs for the same company, pulls prior analysis and compares: guidance vs actual, kill conditions, assumption status. | Delta report with thesis intact flag | 20 to 30 sec |

Total pipeline time: 5 to 8 minutes from transcript to finished episode. ElevenLabs audio is the bottleneck. Steps 7 through 9 add less than 60 seconds total.

For Spanish: Step 5b adapts the script (not direct translation) and Step 6 reruns with Spanish voices, adding 4 to 6 minutes.

---

## 3. Architecture

The pipeline is linear. Each step feeds the next sequentially. Steps 1 through 6 produce the podcast. Steps 7 through 9 produce the governance layer. All intermediate outputs and decisions persist in Supabase.

```
Transcript (paste, upload, or auto fetch by ticker)
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

    === GOVERNANCE LAYER (NEW) ===

All upstream outputs
    |
    v
[7. IC Memo Generator] ------------> structured memo + 1/10 scores
    |                                     |
    v                                     v
[8. Decision Log] ------> Supabase (append only)
    |
    v
[9. Thesis Tracker] ----> delta report (on repeat runs)
    |
    v
Kill condition monitor ---> alerts if thesis breaks
```

---

## 4. Step 1: Transcript Ingestion

Accepts the earnings call in three ways:

**Option A: Paste text.** User copies transcript from any source and pastes it. Works for any company, any quarter.

**Option B: Upload PDF.** User uploads a PDF. Tool extracts text.

**Option C: Enter ticker.** User types a ticker (e.g., MSFT, DUOL, TSMC). Tool uses web search to find and fetch the latest transcript.

The LLM then performs two tasks simultaneously:

**Task A: Claims Extraction.** Pull every material assertion: revenue, growth rates, margin targets, competitive positioning, capex justification, strategic pivots. Each claim gets a category tag.

**Task B: Concept Identification.** For each claim, identify terms and concepts a newcomer would not understand. This is the key differentiator. The LLM acts as a teacher who can see what a student does not know yet.

| Company Type | Example Claim | Concepts Needing Explanation |
|-------------|--------------|------------------------------|
| Cloud/SaaS | ARR grew 35% to $2.1B with 130% NRR | What ARR means, what NRR is, why NRR above 100% signals expansion without new customers |
| Consumer Retail | Same store sales grew 4% with 200bps of margin expansion | What same store sales measures vs total revenue, what basis points are, why margin matters more than topline |
| Fintech/Bank | Net interest margin expanded to 5.7% on $37B deposits | What NIM is, how banks make money on the spread, what deposit cost means, why NIM width matters |
| Semiconductor | Backlog reached $60B with book to bill above 1.0 | What backlog represents, what book to bill ratio indicates, why it can mislead during shortage cycles |
| Pharma/Biotech | Phase 3 readout expected Q2 with pSNS endpoint | What clinical trial phases mean, what a primary endpoint is, how approval probability changes by phase |

---

## 5. Step 2: Business Model Decoder

The most important step for podcast quality. Transforms raw concepts into a teaching sequence from scratch, regardless of company or industry.

### Dependency Mapping

Some concepts depend on others. The decoder maps dependencies and orders explanations so each builds on the last. This ordering is industry specific. For SaaS: recurring revenue before ARR, ARR before NRR, NRR before the growth claim. For a bank: deposits before NIM, NIM before credit risk, credit risk before provisions.

### Analogy Generation

| Industry | Concept | Analogy |
|----------|---------|---------|
| E commerce | Marketplace take rate rising | Like a landlord raising rent every year while promising foot traffic will make up for it |
| SaaS | Net revenue retention 130% | Like a gym where every member not only renews but upgrades to a more expensive plan each year |
| Banking | Net interest margin | The spread between what the bank pays you for deposits and charges borrowers is how banks eat |
| Pharma | Phase 3 clinical trial | Like a student who passed the midterm. Good sign, but the final exam is a different test entirely |
| Hardware | Gross margin expansion via mix shift | Like a restaurant making more money not by raising prices but by selling more cocktails and fewer sodas |

Output: An ordered list of 15 to 25 concept explanations, each with: plain language definition, why it matters for this specific company, a concrete analogy, and which claims it unlocks. The sequence adapts entirely to the company and industry.

---

## 6. Step 3: Bearish Critic

For each major claim (typically 8 to 12 per call), the model applies five lenses of structured skepticism. These work for any company:

**Lens 1: Metric Selection.** Is the number cherry picked? Gross sales instead of net revenue? Adjusted EBITDA excluding stock comp? ARR instead of recognized revenue? Annualized run rate from one strong quarter?

**Lens 2: Omission Detection.** What did management NOT say? Revenue growth without margins = margins compressed. One geography highlighted, another skipped = that region struggles. Metric definition changed from last quarter = something hidden.

**Lens 3: Assumption Testing.** What must be true for this claim to hold? What macro conditions, competitive dynamics, or execution milestones are implicitly assumed?

**Lens 4: Historical Precedent.** Has a similar claim been made before? Did it hold? Uses web search for real parallels.

**Lens 5: Counter Evidence.** What public data contradicts this? Competitor filings, industry reports, analyst downgrades, short seller reports, regulatory actions. Web search for current information.

---

## 7. Step 4: Sector Context Research

Zooms out from the company to the industry. Uses web search to build two opposing sector narratives. The sector is identified automatically from the transcript.

**Sector Bull Case:** Structural tailwinds for the entire sector. Cloud: digital transformation, AI adoption. Fintech: cash to digital shift. Pharma: aging demographics. Energy: supply constraints.

**Sector Bear Case:** Headwinds threatening the sector. Cloud: overbuilding, commoditization. Fintech: credit cycle risk. Pharma: patent cliffs, pricing regulation. Energy: demand destruction from EVs.

This matters because a company can execute perfectly and still underperform if the sector faces headwinds. The podcast separates company execution from sector dynamics.

---

## 8. Step 5: Podcast Script Generator

Takes all upstream output and writes a 6,500 to 7,500 word script for three voices:

| Voice | Role | Personality | Function |
|-------|------|------------|----------|
| HOST | Moderator and learner | Curious, warm, asks naive questions that are actually smart | Keeps it accessible. Forces jargon explanations. Manages pacing. |
| BULL | Optimistic analyst | Confident, data driven, genuinely believes in the company | Strongest case FOR. Uses data plus independent reasoning. Acknowledges risks. |
| BEAR | Skeptical analyst | Sharp, historically grounded, finds what is missing | Challenges every claim. Identifies omissions. Cites parallels where stories failed. |

> **Critical Rule:** The BEAR is never a cartoon villain. The bear case must be intellectually honest and evidence based. The listener should sometimes think "the bear might be right." If the bear is always wrong, the podcast loses credibility.

---

## 9. Step 6: Audio Generation (ElevenLabs)

Sends script segments to ElevenLabs API with three distinct voices. Concatenates into single MP3.

Audio assembly: Split script by speaker tag. Send each to ElevenLabs. Add 300ms silence between turns, 800ms between acts. Concatenate into MP3.

Flash model option: Use Flash (0.5 credits/char) instead of Multilingual v2 (1 credit/char) to double episode capacity within the same quota.

---

## 10. Voice Configuration

| Parameter | HOST | BULL | BEAR |
|-----------|------|------|------|
| Voice Style | Warm, conversational | Confident, energetic | Measured, precise |
| Suggested Voice | Rachel or Adam | Antoni or Josh | Clyde or Arnold |
| Speed | 1.0x (natural) | 1.05x (enthusiastic) | 0.95x (deliberate) |
| Stability | 0.5 | 0.4 (expressive) | 0.6 (consistent) |
| Model | eleven_multilingual_v2 | eleven_multilingual_v2 | eleven_multilingual_v2 |

Spanish voices: Different voice IDs with Latin American accent. Same structure. ElevenLabs multilingual_v2 supports native Spanish.

---

## 11. Script Structure and Pacing

Every episode follows the same seven act structure regardless of company:

| Act | Min | Content | Voices |
|-----|-----|---------|--------|
| 1. Cold Open | 2 | Hook with the most surprising finding. "Company X just reported. Here is what nobody is talking about..." | HOST only |
| 2. Business 101 | 10 | Explain business model from scratch. Revenue sources, how money flows. Uses concept explanations from Step 2. | HOST asks, BULL explains, BEAR adds nuance |
| 3. What Mgmt Said | 5 | Walk through 5 to 8 biggest claims. Present them fairly as stated. | HOST reads, BULL provides context |
| 4. The Debate | 18 | Core of the episode. Claim by claim. BULL makes case. BEAR attacks. HOST asks clarifying questions. | Equal BULL and BEAR, HOST moderates |
| 5. Sector Zoom Out | 5 | Step back. Industry forces that could make or break all companies in this space. | BULL: tailwinds, BEAR: headwinds |
| 6. So What? | 3 | Each analyst's bottom line. No price targets. Frame what you bet on if you own this stock. | BULL then BEAR, 90 sec each |
| 7. Close | 2 | HOST summarizes key tension. Does not pick a side. Leaves listener with the one question that matters. | HOST only |

Pacing Rules: No speaker talks more than 90 seconds without interruption. HOST asks "wait, what does that mean?" every 3 minutes minimum. Tone alternates between serious analysis and lighter moments. Every technical concept gets a concrete example within 30 seconds.

---

## 12. Spanish Episode Adaptation

The Spanish episode is an adaptation, not a translation:

**Analogies change.** Each rewritten for Latin American audiences. Walmart becomes MercadoLibre or Falabella. U.S. banking references become Bancolombia or Nubank.

**Cultural references shift.** Industry context localized. Cloud: LatAm penetration rates. Fintech: Pix (Brazil), Nequi (Colombia), CoDi (Mexico).

**Financial literacy calibration.** Concepts like PE ratio or FCF may need slightly more scaffolding for audiences where retail investing culture is newer.

**Tone.** Slightly warmer and more relational to match LatAm business conversation style, without losing analytical rigor.

---

## 13. Example Script Fragments

### Fragment A: Cloud/SaaS Company

**HOST:** Let's start with something basic. They keep talking about "net revenue retention of 130%." What does that mean?

**BULL:** Think of it like a gym. Imagine 100 members paying $100 each at the start of the year. Some quit. But the ones who stay upgrade to premium, add personal training, buy supplements. End of year, that same group pays $130. 130% retention. You grew 30% without a single new customer.

**HOST:** That sounds incredible. What is the catch?

**BEAR:** NRR is a lagging indicator. It tells you what happened with last year's customers, not what is happening now. If they are landing smaller customers who expand less, NRR starts falling in 12 months. Management knows this before you do.

### Fragment B: Semiconductor Company

**HOST:** They mentioned book to bill ratio of 1.2. What does that mean?

**BULL:** Book to bill compares new orders versus products shipping out. Above 1.0 means more orders arriving than shipping. 1.2 means for every $100 of chips shipped, $120 of new orders arrive. Strong demand.

**HOST:** So higher is always better?

**BEAR:** Not always. In 2021, every chip company had ratios above 1.5 because customers were panic ordering during the shortage. Then the shortage ended, orders got canceled, inventories piled up. A high book to bill can mean genuine demand or customers double ordering out of fear. You do not know which until it is too late.

---

## 14. Step 7: IC Memo Generator (NEW)

The bridge between understanding a company and making a decision about it. Takes all upstream output (claims, explanations, critiques, sector context, podcast script) and compresses it into a structured investment committee memo.

### Memo Structure

**Thesis Summary.** Two sentences maximum. What is the bet and why now. Forces clarity.

**Bull Score (1 to 10).** How compelling is the bull case based on evidence quality, not gut feel. A 9 or 10 means the data overwhelmingly supports the thesis with minimal assumptions. A 5 or 6 means the case is reasonable but depends on execution or macro conditions that could go either way. A 1 or 2 means the bull case relies on hope.

**Bear Score (1 to 10).** How compelling is the bear case. Scored on the same scale. A high bear score does not mean the stock will fall. It means the risks are well evidenced and structurally difficult for management to control. A stock can have a bull score of 8 and a bear score of 7. That means the opportunity is real but so are the risks. The gap between the two scores is what drives position sizing.

**Key Assumptions (ranked).** Three to five assumptions that must hold for the thesis to work, ordered from highest to lowest conviction. Each assumption gets its own 1 to 10 confidence rating. These become the inputs for the thesis tracker in future quarters.

**Kill Conditions.** Specific, measurable conditions that would invalidate the thesis. Not vague statements like "the macro gets worse." Concrete triggers like "NRR drops below 110%" or "management guides below 15% revenue growth for two consecutive quarters" or "net debt to EBITDA exceeds 3.0x." Each kill condition maps to a metric and threshold stored in Supabase for automated monitoring.

**Suggested Position Size.** Expressed as a percentage of total portfolio. Derived from the gap between bull and bear scores, assumption confidence, and number of active kill conditions. Not a recommendation. A structured starting point for the decision.

**Time Horizon.** How long the thesis needs to play out: 6 months, 12 months, or 18+ months.

### Scoring Calibration Guide

| Score | Label | What It Means |
|-------|-------|---------------|
| 1 to 2 | Weak | Case relies on hope, narrative, or a single data point. No structural advantage or evidence is thin. |
| 3 to 4 | Below average | Some supporting data but significant gaps. Multiple assumptions need to break right. |
| 5 to 6 | Moderate | Reasonable case. Execution dependent. Could go either way based on macro or competition. |
| 7 to 8 | Strong | Well evidenced. Structural advantages visible. Few assumptions required. Clear catalyst. |
| 9 to 10 | Exceptional | Overwhelming evidence. Rare. Requires multiple independent data points all confirming the same thesis. |

The LLM generates the memo automatically after the podcast script. The user reviews and can override any score before logging a decision. Override history is tracked so you can calibrate your own judgment against the model's over time.

---

## 15. Step 8: Decision Log (NEW)

An append only record of every investment decision. This is the accountability backbone of the entire system. Every hedge fund has a decision log. Almost no individual investor does. It is the single biggest process edge you can give yourself because it turns investing from a series of disconnected bets into a system with memory.

### What Gets Logged

**Action.** One of: buy, add, trim, exit, pass, hold. "Pass" is as important as "buy" because it captures ideas you evaluated and deliberately chose not to act on. Six months later, you can check whether passing was right.

**Conviction (1 to 10).** Your personal conviction at the time of the decision, separate from the model's bull/bear scores. Over time, comparing your conviction scores against actual outcomes reveals whether you are well calibrated or systematically overconfident.

**Rationale.** In your own words, why this action. Not the model's summary. Your reasoning. This is what you read during post mortems to understand your own decision making patterns.

**Price at Decision.** The price when you made the call. Not the execution price (which may differ). This anchors the decision to a moment in time.

**Size.** Actual position size as percentage of portfolio. Compare this to the memo's suggested size to track whether you consistently size up or down relative to the model's recommendation.

The log is append only. You never edit or delete past entries. If your view changes, you add a new entry with the updated action. The full history of how your thinking evolved is the point.

---

## 16. Step 9: Thesis Tracker (NEW)

Closes the feedback loop. When you run the pipeline again for a company you have previously analyzed, this step automatically pulls the prior analysis and IC memo from Supabase and generates a delta report.

### Delta Report Contents

**Guidance vs Actual.** For each metric management guided on last quarter, compare what they said would happen to what actually happened. Output is a structured array of {metric, guided value, actual value, delta, assessment}. This builds a management credibility score over time.

**Assumption Status.** Each assumption from the prior IC memo is re evaluated: held, weakened, or broken. An assumption rated 8/10 confidence that turns out to be wrong is a learning signal.

**Kill Condition Check.** Every active kill condition is evaluated against the new data. If triggered, the status updates to "triggered" with a timestamp and the run that detected it. This is the most important output: when a kill condition fires, the system explicitly flags it and generates a recommended action.

**Bull/Bear Case Evolution.** How did each side of the debate change? Did the bear risks get worse or resolve? Did the bull catalysts arrive or get delayed?

**Thesis Intact Flag.** A simple boolean plus narrative: is the original thesis still valid? If no, what changed? This forces an explicit decision: hold, add, trim, or exit. That decision feeds back into the Decision Log (Step 8).

The thesis tracker makes the system recursive. Each quarter's analysis builds on the last. Over four or five quarters, you have a complete institutional record of how your understanding of a company evolved, where your assumptions held or broke, and whether management deserves your trust.

---

## 17. Supabase Database Schema (NEW)

Seven tables. Designed for a single user with row level security enabled from day one so the schema scales to multiple users without restructuring.

### Table: companies

Reference table. One row per ticker, created on first pipeline run for that company.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| ticker | text, unique | MSFT, SOFI, EWZ etc |
| name | text | Microsoft Corp |
| sector | text | Cloud/SaaS, Fintech, Energy |
| first_analyzed_at | timestamptz | Auto set on insert |
| notes | text, nullable | Free form context you want to persist |

### Table: analysis_runs

One row every time the pipeline executes. The spine that connects everything. Intermediate LLM outputs stored as jsonb to avoid constant migrations as prompts evolve.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| company_id | uuid, FK > companies | |
| quarter | text | Q1 2026, Q4 2025 |
| run_date | timestamptz | When pipeline executed |
| transcript_source | text | paste, upload, auto_fetch |
| claims_json | jsonb | Raw output from Step 1 |
| concepts_json | jsonb | Concept glossary from Step 1 |
| explanations_json | jsonb | Ordered sequence from Step 2 |
| critiques_json | jsonb | Bear critiques from Step 3 |
| sector_context_json | jsonb | Bull + bear sector from Step 4 |
| script_en | text, nullable | Full English script |
| script_es | text, nullable | Full Spanish script |
| audio_en_url | text, nullable | Link to English MP3 |
| audio_es_url | text, nullable | Link to Spanish MP3 |
| status | text | running, completed, failed |
| duration_seconds | integer, nullable | Total pipeline time |

### Table: ic_memos

One memo per analysis run. The Step 7 output. All conviction scores use 1 to 10 scale.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| run_id | uuid, FK > analysis_runs | |
| company_id | uuid, FK > companies | |
| thesis_summary | text | Two sentence thesis |
| bull_score | integer | 1 to 10 conviction |
| bear_score | integer | 1 to 10 conviction |
| key_assumptions | jsonb | Array of {text, confidence_1_10} |
| suggested_size_pct | numeric | e.g. 3.5 for 3.5% of portfolio |
| time_horizon | text | 6 months, 12 months, 18+ months |
| memo_text | text | Full formatted memo |
| created_at | timestamptz | |

### Table: decisions

Append only log. One row per decision event. All conviction scores use 1 to 10 scale.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| company_id | uuid, FK > companies | |
| memo_id | uuid, FK > ic_memos, nullable | Null if no formal memo |
| decision_date | date | |
| action | text | buy, add, trim, exit, pass, hold |
| size_pct | numeric, nullable | Actual position size taken |
| price_at_decision | numeric, nullable | Price when decision was made |
| rationale | text | In your own words |
| conviction | integer | 1 to 10 |
| created_at | timestamptz | |

### Table: kill_conditions

Separate table because each thesis has multiple kill conditions and each needs independent tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| memo_id | uuid, FK > ic_memos | |
| company_id | uuid, FK > companies | |
| condition_text | text | "NRR drops below 110%" |
| metric_name | text, nullable | nrr, gross_margin, revenue_growth |
| threshold_value | numeric, nullable | 110, 0.35, 0.15 |
| threshold_direction | text, nullable | below, above |
| status | text | active, triggered, cleared, retired |
| triggered_at | timestamptz, nullable | When it fired |
| triggered_by_run_id | uuid, FK > analysis_runs, nullable | Which run detected it |
| notes | text, nullable | Context when status changes |
| created_at | timestamptz | |

### Table: thesis_reviews

The delta report. Created when you run the pipeline on a company that already has a prior analysis.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| current_run_id | uuid, FK > analysis_runs | This quarter's run |
| prior_run_id | uuid, FK > analysis_runs | Last quarter's run |
| company_id | uuid, FK > companies | |
| guidance_vs_actual | jsonb | {metric, guided, actual, delta} |
| assumptions_status | jsonb | Each assumption: held, weakened, broken |
| kill_conditions_status | jsonb | Snapshot at review time |
| bear_case_evolution | text | How the bear case changed |
| bull_case_evolution | text | How the bull case changed |
| thesis_still_intact | boolean | Bottom line call |
| recommended_action | text | hold, add, trim, exit, revisit |
| review_text | text | Full narrative delta report |
| created_at | timestamptz | |

### Table: analysis_chunks

RAG ready decomposition of each pipeline run. Every claim, concept, critique, sector narrative, assumption, and kill condition gets its own row with a consistent metadata envelope. The embedding column stays null until you enable RAG. One pipeline run produces 60 to 80 rows, each containing a single coherent idea (50 to 200 words), which is the sweet spot for embedding quality.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid, PK | |
| run_id | uuid, FK > analysis_runs | |
| company_id | uuid, FK > companies | |
| chunk_type | text | claim, concept, critique, sector_bull, sector_bear, assumption, kill_condition, thesis_summary, delta_observation |
| chunk_text | text | One idea per row, 50 to 200 words |
| metadata | jsonb | {ticker, quarter, category, score, metric_name, related_claim_ids} |
| embedding | vector(1536), nullable | Null until RAG is enabled, then backfill |
| created_at | timestamptz | |

### Table Relationships

```
companies (1) ------> (many) analysis_runs
companies (1) ------> (many) decisions
analysis_runs (1) --> (1)    ic_memos
analysis_runs (1) --> (many) analysis_chunks
ic_memos (1) -------> (many) kill_conditions
ic_memos (1) -------> (0..1) decisions
analysis_runs (1) --> (many) thesis_reviews (as current or prior)
```

### Design Decisions

**jsonb columns in analysis_runs.** The intermediate LLM outputs are semi structured and their schema will evolve as you tune prompts. Forcing them into rigid columns now would mean constant migrations. Store them as jsonb, query them when needed, and only promote a field to its own column if you find yourself filtering or joining on it repeatedly.

**Row Level Security.** Supabase RLS means you can lock everything to your user ID from day one. If you ever open this up to other users or build a shared version, the auth layer is already in place.

**1 to 10 scoring throughout.** All conviction, bull, bear, and assumption confidence scores use a 1 to 10 integer scale for consistency. This gives enough granularity to distinguish between "moderate" (5/6) and "strong" (7/8) without the false precision of decimals.

**Dual storage: jsonb blobs + individual chunks.** The analysis_runs table keeps the full jsonb blobs for pipeline reconstruction and debugging. The analysis_chunks table decomposes the same data into individually addressable rows for retrieval. This is intentional duplication. The blobs serve the pipeline. The chunks serve RAG. Trying to make one structure do both creates compromises in both directions.

**Chunking at write time, not retroactively.** The pipeline writes chunks during execution, not as a batch migration later. Retrofitting chunks from jsonb blobs after the fact means parsing inconsistent structures, guessing at boundaries, and hoping the splitting logic matches what the pipeline would have produced. Writing chunks at pipeline time guarantees consistency and costs almost nothing (30 lines of code, 0.5 seconds per run).

**Embedding column null by default.** The vector(1536) column exists from day one but stays null until you have enough data to justify RAG (roughly 3+ companies with 2+ quarters each). When ready, backfill embeddings in a single batch job and enable pgvector similarity search. No schema migration required.

---

## 18. RAG Ready: Analysis Chunks (NEW)

### Why Chunks Matter

The pipeline produces highly structured analytical output at every step. Claims with category tags, critiques with evidence, scored assumptions, kill conditions with thresholds. This is pre analyzed, pre categorized content, not raw text. RAG over structured analytical output is dramatically more useful than RAG over raw transcripts.

But the jsonb blobs in analysis_runs are too large for effective retrieval. A single critiques_json column contains 8 to 12 critiques covering different topics. Embedding the entire blob produces a vector that tries to represent too many ideas at once. A query about "margin compression risk" returns the entire critiques blob when you only needed one specific critique.

The analysis_chunks table solves this by decomposing each run into individually embeddable rows, each containing a single coherent idea.

### What Gets Chunked

Each pipeline run produces approximately 60 to 80 chunks:

| Source Step | Chunk Type | Typical Count | Typical Length |
|-------------|-----------|---------------|----------------|
| Step 1 | claim | 15 to 20 | 50 to 100 words |
| Step 1 | concept | 15 to 25 | 30 to 80 words |
| Step 3 | critique | 8 to 12 | 100 to 200 words |
| Step 4 | sector_bull | 1 | 150 to 250 words |
| Step 4 | sector_bear | 1 | 150 to 250 words |
| Step 7 | assumption | 3 to 5 | 50 to 100 words |
| Step 7 | kill_condition | 3 to 5 | 30 to 60 words |
| Step 7 | thesis_summary | 1 | 30 to 50 words |
| Step 9 | delta_observation | 3 to 8 | 80 to 150 words |

### Metadata Envelope

Every chunk carries a standardized metadata jsonb with: ticker, quarter, chunk_type, and any relevant context (category tag for claims, score for assumptions, metric name for kill conditions, related claim IDs for critiques). This enables hybrid queries: SQL WHERE clause filters by company, quarter, and chunk type, then pgvector similarity search ranks within the filtered subset.

### What NOT to Chunk

The podcast script (6,500 to 7,500 words) is a final output, not a retrieval source. The analytical content is already captured in the structured chunks upstream. The script is for listening, not for querying. The IC memo full text is designed to be read as a whole. Its individual components (assumptions, kill conditions, thesis summary) are already chunked separately.

### Query Patterns (When RAG is Enabled)

**Structured queries (SQL, no embeddings):** Bull/bear scores, conviction ratings, kill condition statuses, assumption confidence scores, position sizes, decision history, guidance vs actual deltas. Covers roughly 60% of portfolio level questions.

**Semantic queries (pgvector similarity):** "Which of my holdings faces similar margin pressure to what SOFI reported?" "Are any of my bull theses contradicting each other?" "What sector headwinds are showing up across multiple companies?" Covers the remaining 40% where you're looking for thematic connections across companies.

**Hybrid queries (SQL filter + vector search):** "Find all critiques for companies in my portfolio from the last two quarters that are semantically similar to margin compression." SQL filters to the right chunk_type, ticker set, and quarter range, then vector similarity ranks within that subset. This is where the metadata envelope pays off.

### When to Enable RAG

Not on day one. Build the pipeline, write chunks at every run, leave embeddings null. Enable RAG after you have at least 3 companies with 2+ quarters of data each. The trigger is when you catch yourself thinking "I remember reading something similar in another analysis but I cannot find it." At that point: enable pgvector in Supabase (one click), run a backfill script to generate embeddings for all existing chunks, and build a query function that routes between SQL and vector search. Maybe 200 lines of code and half a day of work.

---

## 19. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | Python (sequential pipeline) | Run 9 steps in order |
| LLM (Steps 1,2,4,5,7) | Claude Sonnet 4 via API | Extraction, decoding, context, script, memo |
| LLM (Step 3) | Claude Opus 4 via API | Deep critique (strongest reasoning needed) |
| LLM (Step 9) | Claude Sonnet 4 via API | Delta report generation |
| Web Search | Claude API web_search tool | Counter evidence, sector research, current data |
| Audio (Step 6) | ElevenLabs API multilingual_v2 | Three voice podcast in EN and ES |
| Audio Processing | pydub (Python) | Concatenate, add silence, export MP3 |
| Database (NEW) | Supabase (PostgreSQL + pgvector) | Persist all runs, memos, decisions, chunks |
| Vector Search (NEW) | pgvector extension in Supabase | Semantic similarity over analysis chunks |
| Auth (NEW) | Supabase Auth + RLS | User scoped data access |
| UI (Option A) | Claude Artifact (React) | Zero cost, runs inside Claude |
| UI (Option B) | Streamlit | Standalone deployed app |

---

## 20. Cost Analysis

### Claude Artifact Version

| Item | Cost | Notes |
|------|------|-------|
| Claude LLM (Steps 1 to 7, 9) | $0 | Covered by Claude subscription |
| Web search | $0 | Built into Claude API |
| ElevenLabs audio (Step 6) | $0 | Covered by ElevenLabs subscription |
| Supabase (NEW) | $0 | Free tier: 500MB DB, 50K auth users, pgvector included |
| Hosting | $0 | Runs inside Claude |
| **TOTAL** | **$0 extra** | Uses existing subscriptions only |

### ElevenLabs Quota per Plan

One 45 min episode = ~35,000 characters. Bilingual (EN + ES) = ~70,000 characters.

| Plan | Monthly Chars | EN Episodes/Mo | EN+ES Episodes/Mo |
|------|--------------|----------------|-------------------|
| Starter ($5) | 30,000 | 0 (not enough) | 0 |
| Creator ($22) | 100,000 | 2 | 1 |
| Pro ($99) | 500,000 | 14 | 7 |
| With Flash model | 2x above | 2x above | 2x above |

### Standalone Streamlit Version

| Item | Per Episode | Monthly (4 eps) | Notes |
|------|------------|----------------|-------|
| Claude Sonnet | $0.40 to $0.80 | $1.60 to $3.20 | ~50K in + 10K out tokens |
| Claude Opus | $1.50 to $2.50 | $6 to $10 | ~30K in + 5K out tokens |
| ElevenLabs | $0 | $0 | Covered by subscription |
| Supabase | $0 | $0 | Free tier sufficient |
| Hosting | N/A | $0 to $20 | Streamlit Cloud or Railway |
| **TOTAL** | **$1.90 to $3.30** | **$7.60 to $33.20** | |

---

## 21. Development Phases

| Phase | Scope | Deliverable | Days |
|-------|-------|------------|------|
| 1. Script Pipeline | Steps 1 through 5. Full prompt chain from transcript to script. Test across 5+ companies. | Python script outputting a podcast script from any transcript | 4 to 5 |
| 2. Audio Generation | Step 6. ElevenLabs integration, speaker segmentation, silence insertion, MP3 export. | Pipeline converting script to finished MP3 | 2 to 3 |
| 3. Spanish | Step 5b and 6b. Adaptation prompt, Spanish voice selection, cultural calibration. | Bilingual pipeline producing EN + ES | 2 to 3 |
| 4. Governance (NEW) | Steps 7 through 9. IC memo generation, decision logging, thesis tracking prompts. | Full governance pipeline with Supabase | 3 to 4 |
| 5. Database (NEW) | Supabase setup. Seven tables including analysis_chunks, RLS policies, pgvector extension, API integration with pipeline. | Working persistence layer with RAG ready chunks | 2 to 3 |
| 6. UI | Streamlit or Artifact. Transcript input, progress, audio player, memo display, decision form. | Working app with playback and governance views | 3 to 4 |
| 7. Polish | Prompt tuning across diverse companies. Voice fine tuning. Governance UX. Edge cases. | Production v1.0 | 3 to 4 |

Total: 19 to 26 days. Phase 1 remains 60% of the effort. Governance adds 4 to 6 days. Chunking adds minimal overhead (built into Phase 5).

Recommended: Build Phase 1 inside Claude as an artifact first (zero cost). Validate quality across companies. Add governance (Phase 4 and 5) once the podcast pipeline is solid. Then decide whether to keep artifact or build full Streamlit app. RAG enablement is a future half day task once you have enough data.

---

## 22. Build Options: Claude Artifact vs Streamlit

| Dimension | Claude Artifact | Streamlit App |
|-----------|----------------|---------------|
| LLM cost | $0 (subscription) | Paid API calls |
| ElevenLabs | User provides key in browser | Key in server environment |
| Supabase | Direct client SDK from artifact | Server side Python client |
| Audio playback | HTML5 player in artifact | st.audio component |
| Governance UI | React components for memo + log | Streamlit forms and tables |
| File download | Browser download link | st.download_button |
| Sharing | Share Claude chat link | Share app URL |
| Maintenance | Zero | Monitor + update dependencies |
| Setup effort | 8 to 12 days | 18 to 25 days |
| Best for | Personal use, prototyping | Shared use, polished experience |

Recommendation: Build the Claude artifact version first. 85% of the value at zero extra cost and 40% of the development time. The governance layer (Steps 7 through 9) works in both environments since Supabase is accessible from either a React artifact or a Streamlit backend. Use it for a month across different companies. If you need a polished shared experience, then invest in the Streamlit version.

**Ready for implementation.**
