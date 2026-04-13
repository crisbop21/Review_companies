-- RAG-ready decomposition. Every pipeline run emits 60-80 chunks with
-- standardized metadata. The embedding column is nullable so rows can be
-- written today and backfilled when RAG is enabled (Migration 009).
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
