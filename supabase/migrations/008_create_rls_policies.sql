-- Row-level security: every table is user-scoped. Each policy allows a user
-- to read and write only their own rows. Service-role keys bypass RLS as
-- usual for server-side admin tasks.

alter table companies         enable row level security;
alter table analysis_runs     enable row level security;
alter table ic_memos          enable row level security;
alter table decisions         enable row level security;
alter table kill_conditions   enable row level security;
alter table thesis_reviews    enable row level security;
alter table analysis_chunks   enable row level security;

-- companies
create policy "companies: select own"  on companies
  for select using (auth.uid() = user_id);
create policy "companies: insert own"  on companies
  for insert with check (auth.uid() = user_id);
create policy "companies: update own"  on companies
  for update using (auth.uid() = user_id);

-- analysis_runs
create policy "runs: select own"  on analysis_runs
  for select using (auth.uid() = user_id);
create policy "runs: insert own"  on analysis_runs
  for insert with check (auth.uid() = user_id);
create policy "runs: update own"  on analysis_runs
  for update using (auth.uid() = user_id);

-- ic_memos
create policy "memos: select own"  on ic_memos
  for select using (auth.uid() = user_id);
create policy "memos: insert own"  on ic_memos
  for insert with check (auth.uid() = user_id);
create policy "memos: update own"  on ic_memos
  for update using (auth.uid() = user_id);

-- decisions (append-only: no UPDATE policy by design)
create policy "decisions: select own"  on decisions
  for select using (auth.uid() = user_id);
create policy "decisions: insert own"  on decisions
  for insert with check (auth.uid() = user_id);

-- kill_conditions
create policy "kill: select own"  on kill_conditions
  for select using (auth.uid() = user_id);
create policy "kill: insert own"  on kill_conditions
  for insert with check (auth.uid() = user_id);
create policy "kill: update own"  on kill_conditions
  for update using (auth.uid() = user_id);

-- thesis_reviews
create policy "reviews: select own"  on thesis_reviews
  for select using (auth.uid() = user_id);
create policy "reviews: insert own"  on thesis_reviews
  for insert with check (auth.uid() = user_id);

-- analysis_chunks
create policy "chunks: select own"  on analysis_chunks
  for select using (auth.uid() = user_id);
create policy "chunks: insert own"  on analysis_chunks
  for insert with check (auth.uid() = user_id);
create policy "chunks: update own"  on analysis_chunks
  for update using (auth.uid() = user_id);
