-- One row per pipeline execution. All intermediate outputs stored as jsonb
-- so reruns, audits, and the chunker can operate from a single source of truth.
create table analysis_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  company_id uuid references companies(id) not null,
  quarter text not null,
  run_date timestamptz default now(),
  transcript_source text not null,

  -- Intermediate step outputs
  claims_json jsonb,
  concepts_json jsonb,
  explanations_json jsonb,
  critiques_json jsonb,
  sector_context_json jsonb,

  -- Final artifacts
  script_en text,
  script_es text,
  audio_en_url text,
  audio_es_url text,

  -- Provenance (added during scaffolding so prompt-version diffs are trackable
  -- from the first run onward; saves weeks of debugging when outputs regress).
  prompt_versions jsonb default '{}'::jsonb,
  model_versions  jsonb default '{}'::jsonb,

  status text not null default 'running',
  duration_seconds integer
);

create index idx_runs_company on analysis_runs(company_id);
create index idx_runs_quarter on analysis_runs(quarter);
