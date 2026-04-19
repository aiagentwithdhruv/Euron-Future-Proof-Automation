-- RAG Knowledge Chatbot — Supabase pgvector schema
-- Run once in Supabase SQL editor. Idempotent.
--
-- Embedding dim default = 768 (Gemini text-embedding-004 / "Gemini Embedding 2").
-- If you switch to gemini-embedding-001 (3072 dims), change vector(768) to vector(3072)
-- and drop + recreate the index.

create extension if not exists vector;

create table if not exists knowledge_chunks (
    id              bigserial primary key,
    chunk_id        text unique not null,
    source_id       text not null,
    source_path     text not null,
    section         text,
    chunk_index     int not null,
    content         text not null,
    token_estimate  int,
    metadata        jsonb not null default '{}'::jsonb,
    embedding       vector(768),
    updated_at      timestamptz not null default now(),
    created_at      timestamptz not null default now()
);

create index if not exists knowledge_chunks_source_idx
    on knowledge_chunks (source_id);

-- Cosine similarity index. IVFFlat is fine for <100k rows; HNSW better above that.
create index if not exists knowledge_chunks_embedding_idx
    on knowledge_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- Similarity search RPC. Returns top-k chunks with cosine similarity (0..1 where 1 = identical).
create or replace function match_chunks(
    query_embedding vector(768),
    match_count int default 5,
    source_filter text default null
)
returns table (
    chunk_id     text,
    source_id    text,
    source_path  text,
    section      text,
    chunk_index  int,
    content      text,
    metadata     jsonb,
    similarity   float
)
language sql stable
as $$
    select
        kc.chunk_id,
        kc.source_id,
        kc.source_path,
        kc.section,
        kc.chunk_index,
        kc.content,
        kc.metadata,
        1 - (kc.embedding <=> query_embedding) as similarity
    from knowledge_chunks kc
    where (source_filter is null or kc.source_id = source_filter)
      and kc.embedding is not null
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;

-- Feedback table for the learn loop.
create table if not exists feedback_events (
    id            bigserial primary key,
    query         text not null,
    answer        text,
    citations     jsonb,
    confidence    float,
    verdict       text check (verdict in ('up','down','escalated')),
    user_note     text,
    channel       text,
    created_at    timestamptz not null default now()
);

-- Chat sessions (for n8n chat memory across turns).
create table if not exists chat_sessions (
    id         bigserial primary key,
    session_id text not null,
    role       text not null check (role in ('user','assistant','system')),
    content    text not null,
    created_at timestamptz not null default now()
);
create index if not exists chat_sessions_session_idx on chat_sessions (session_id, created_at);
