-- Enable pgvector so the embedding column on analysis_chunks becomes usable.
-- The IVFFlat index below is commented out intentionally; creating it on an
-- empty table is wasted work. Uncomment and run once embeddings exist.

create extension if not exists vector;

-- create index idx_chunks_embedding on analysis_chunks
--   using ivfflat (embedding vector_cosine_ops) with (lists = 100);
