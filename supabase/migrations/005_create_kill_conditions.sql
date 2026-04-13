-- Measurable conditions that would invalidate a thesis. The thesis tracker
-- (Step 9) evaluates status on every repeat run.
create table kill_conditions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null default auth.uid(),
  memo_id uuid references ic_memos(id) not null,
  company_id uuid references companies(id) not null,
  condition_text text not null,
  metric_name text,
  threshold_value numeric,
  threshold_direction text check (threshold_direction in ('below','above')),
  status text not null default 'active'
    check (status in ('active','triggered','cleared','retired')),
  triggered_at timestamptz,
  triggered_by_run_id uuid references analysis_runs(id),
  notes text,
  created_at timestamptz default now()
);

create index idx_kill_status on kill_conditions(status);
create index idx_kill_company on kill_conditions(company_id);
