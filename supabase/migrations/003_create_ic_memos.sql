-- Investment committee memo. 1-10 scored bull/bear cases with ranked
-- assumptions and kill conditions (the latter stored in a separate table).
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

create index idx_memos_run on ic_memos(run_id);
create index idx_memos_company on ic_memos(company_id);
