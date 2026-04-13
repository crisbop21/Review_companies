-- Append-only investment decision log. Never UPDATE or DELETE; instead,
-- write a new row (e.g., buy -> add -> trim -> exit) and let history stand.
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

create index idx_decisions_company on decisions(company_id);
create index idx_decisions_memo on decisions(memo_id);
