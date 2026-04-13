-- Delta reports comparing current-quarter analysis vs. the prior memo.
-- Emitted by Step 9 on repeat runs only.
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

create index idx_reviews_company on thesis_reviews(company_id);
