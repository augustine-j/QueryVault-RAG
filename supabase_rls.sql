-- =====================================================================
-- QueryVault RAG: enable Row-Level Security on all public tables.
--
-- The FastAPI app connects with a privileged connection string
-- (session pooler / postgres role). Table owners bypass RLS by default,
-- so this hardens the tables against the Supabase Data API
-- (anon/authenticated roles) WITHOUT changing any application behavior.
--
-- Run once in Supabase Studio: SQL Editor -> paste -> Run.
-- Verify afterwards under Database -> Tables (RLS icon should be green).
-- =====================================================================

ALTER TABLE public.users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents     ENABLE ROW LEVEL SECURITY;

-- No policies are created here on purpose: with zero policies, the
-- anon/authenticated Data API roles can see no rows even if API access
-- stays enabled. If you never use Supabase client libraries from the
-- browser, you can additionally disable "Data API" exposure under
-- Project Settings -> API settings for defense in depth.
