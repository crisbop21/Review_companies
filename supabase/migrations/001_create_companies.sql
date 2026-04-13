-- One row per ticker, scoped to a user.
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

create index idx_companies_ticker on companies(ticker);
