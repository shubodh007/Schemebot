-- ═══════════════════════════════════════════════════════════════════════
-- GOVSCHEME AI — COMPLETE POSTGRESQL SCHEMA
-- Run this in Supabase SQL Editor to create all tables.
-- ═══════════════════════════════════════════════════════════════════════

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────── TIMESTAMP TRIGGER ───────────────────
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- ─────────────────── ENUM TYPES ───────────────────
DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('citizen', 'admin', 'superadmin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE user_status AS ENUM ('pending_verification', 'active', 'suspended', 'deleted');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE gender_type AS ENUM ('male', 'female', 'other', 'prefer_not_to_say');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE caste_category AS ENUM ('general', 'obc', 'sc', 'st', 'ews', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE disability_type AS ENUM ('none', 'visual', 'hearing', 'locomotor', 'intellectual', 'multiple');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE scheme_level AS ENUM ('central', 'state', 'district', 'local');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE scheme_status AS ENUM ('active', 'inactive', 'expired', 'coming_soon', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE eligibility_op AS ENUM ('eq', 'neq', 'lt', 'lte', 'gt', 'gte', 'in', 'not_in', 'between', 'contains');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE ai_provider_type AS ENUM ('claude', 'openai', 'gemini', 'deepseek', 'groq', 'openrouter');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE document_type AS ENUM ('aadhaar', 'pan', 'voter_id', 'ration_card', 'income_cert', 'caste_cert', 'disability_cert', 'bank_statement', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE document_status AS ENUM ('uploading', 'processing', 'ready', 'failed', 'deleted');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ─────────────────── CORE TABLES ───────────────────

CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               TEXT NOT NULL,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    password_hash       TEXT,
    role                user_role NOT NULL DEFAULT 'citizen',
    status              user_status NOT NULL DEFAULT 'pending_verification',
    failed_login_count  SMALLINT NOT NULL DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    last_login_at       TIMESTAMPTZ,
    last_login_ip       INET,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_email_unique UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name           TEXT NOT NULL,
    phone               TEXT,
    date_of_birth       DATE,
    gender              gender_type,
    caste_category      caste_category,
    disability_status   disability_type NOT NULL DEFAULT 'none',
    disability_percent  SMALLINT CHECK (disability_percent BETWEEN 0 AND 100),
    annual_income       NUMERIC(12,2) CHECK (annual_income >= 0),
    state_code          CHAR(2),
    district            TEXT,
    occupation          TEXT,
    education_level     TEXT,
    is_farmer           BOOLEAN NOT NULL DEFAULT FALSE,
    is_bpl              BOOLEAN NOT NULL DEFAULT FALSE,
    marital_status      TEXT,
    preferred_language  TEXT NOT NULL DEFAULT 'en',
    avatar_url          TEXT,
    profile_complete    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT profile_user_unique UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token    TEXT NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sessions_access_token_unique UNIQUE (access_token)
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    token_hash      TEXT NOT NULL,
    used            BOOLEAN NOT NULL DEFAULT FALSE,
    used_at         TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT refresh_token_hash_unique UNIQUE (token_hash)
);

-- ─────────────────── SCHEME TABLES ───────────────────

CREATE TABLE IF NOT EXISTS scheme_categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL,
    description TEXT,
    icon_name   TEXT,
    parent_id   UUID REFERENCES scheme_categories(id),
    sort_order  SMALLINT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scheme_categories_slug_unique UNIQUE (slug)
);

CREATE TABLE IF NOT EXISTS schemes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id         TEXT,
    title               TEXT NOT NULL,
    title_hi            TEXT,
    title_te            TEXT,
    slug                TEXT NOT NULL,
    description         TEXT NOT NULL,
    description_hi      TEXT,
    description_te      TEXT,
    category_id         UUID NOT NULL REFERENCES scheme_categories(id),
    ministry            TEXT,
    department          TEXT,
    level               scheme_level NOT NULL,
    state_code          CHAR(2),
    status              scheme_status NOT NULL DEFAULT 'active',
    launch_date         DATE,
    end_date            DATE,
    budget_allocated    NUMERIC(15,2),
    beneficiaries_count INTEGER,
    application_url     TEXT,
    guidelines_url      TEXT,
    portal_url          TEXT,
    source_url          TEXT NOT NULL,
    last_scraped_at     TIMESTAMPTZ,
    content_hash        TEXT,
    tags                TEXT[] NOT NULL DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT schemes_slug_unique UNIQUE (slug),
    CONSTRAINT schemes_end_after_launch CHECK (end_date IS NULL OR end_date > launch_date)
);

CREATE TABLE IF NOT EXISTS scheme_eligibility_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scheme_id       UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    field_name      TEXT NOT NULL,
    operator        eligibility_op NOT NULL,
    value           JSONB NOT NULL,
    is_mandatory    BOOLEAN NOT NULL DEFAULT TRUE,
    description     TEXT,
    sort_order      SMALLINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── CONVERSATION TABLES ───────────────────

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT,
    summary         TEXT,
    message_count   INTEGER NOT NULL DEFAULT 0,
    token_count     INTEGER NOT NULL DEFAULT 0,
    ai_provider     ai_provider_type,
    model_name      TEXT,
    is_archived     BOOLEAN NOT NULL DEFAULT FALSE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role                message_role NOT NULL,
    content             TEXT NOT NULL,
    content_hi          TEXT,
    content_te          TEXT,
    ai_provider         ai_provider_type,
    model_name          TEXT,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    latency_ms          INTEGER,
    confidence_score    NUMERIC(4,3) CHECK (confidence_score BETWEEN 0 AND 1),
    citations           JSONB NOT NULL DEFAULT '[]',
    is_partial          BOOLEAN NOT NULL DEFAULT FALSE,
    feedback_score      SMALLINT CHECK (feedback_score BETWEEN 1 AND 5),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── DOCUMENT TABLES ───────────────────

CREATE TABLE IF NOT EXISTS documents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename   TEXT NOT NULL,
    storage_key         TEXT NOT NULL,
    mime_type           TEXT NOT NULL,
    file_size_bytes     BIGINT NOT NULL CHECK (file_size_bytes > 0),
    page_count          INTEGER,
    document_type       document_type NOT NULL DEFAULT 'other',
    status              document_status NOT NULL DEFAULT 'uploading',
    ocr_confidence      NUMERIC(4,3),
    extracted_text      TEXT,
    extracted_fields    JSONB NOT NULL DEFAULT '{}',
    scheme_matches      JSONB NOT NULL DEFAULT '[]',
    error_message       TEXT,
    processing_started  TIMESTAMPTZ,
    processing_finished TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    scheme_id       UUID REFERENCES schemes(id) ON DELETE SET NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    chunk_metadata  JSONB NOT NULL DEFAULT '{}',
    token_count     INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── USER ACTIVITY TABLES ───────────────────

CREATE TABLE IF NOT EXISTS saved_schemes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheme_id       UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    notes           TEXT,
    reminder_date   DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT saved_schemes_unique UNIQUE (user_id, scheme_id)
);

CREATE TABLE IF NOT EXISTS scheme_comparisons (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheme_ids  UUID[] NOT NULL,
    name        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legal_queries (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id     UUID REFERENCES conversations(id) ON DELETE SET NULL,
    query_text          TEXT NOT NULL,
    query_type          TEXT,
    response_text       TEXT,
    citations           JSONB NOT NULL DEFAULT '[]',
    needs_escalation    BOOLEAN NOT NULL DEFAULT FALSE,
    feedback_score      SMALLINT CHECK (feedback_score BETWEEN 1 AND 5),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── SCRAPING TABLES ───────────────────

CREATE TABLE IF NOT EXISTS scraping_jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name         TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    job_type            TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending',
    triggered_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    started_at          TIMESTAMPTZ,
    finished_at         TIMESTAMPTZ,
    pages_scraped       INTEGER NOT NULL DEFAULT 0,
    schemes_found       INTEGER NOT NULL DEFAULT 0,
    schemes_updated     INTEGER NOT NULL DEFAULT 0,
    schemes_new         INTEGER NOT NULL DEFAULT 0,
    error_count         INTEGER NOT NULL DEFAULT 0,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── ANALYTICS TABLES ───────────────────

CREATE TABLE IF NOT EXISTS analytics_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type      TEXT NOT NULL,
    event_data      JSONB NOT NULL DEFAULT '{}',
    session_id      TEXT,
    ip_hash         TEXT,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    target_type     TEXT NOT NULL,
    target_id       UUID NOT NULL,
    score           SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────── INDEXES ───────────────────

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_state ON user_profiles(state_code);
CREATE INDEX IF NOT EXISTS idx_profiles_caste ON user_profiles(caste_category);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_schemes_category ON schemes(category_id);
CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes(level);
CREATE INDEX IF NOT EXISTS idx_schemes_state ON schemes(state_code);
CREATE INDEX IF NOT EXISTS idx_schemes_status ON schemes(status);
CREATE INDEX IF NOT EXISTS idx_schemes_tags ON schemes USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_eligibility_scheme ON scheme_eligibility_rules(scheme_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_saved_user_id ON saved_schemes(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_user_id ON legal_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_feedback_target ON feedback(target_type, target_id);

-- ─────────────────── TRIGGERS ───────────────────

DROP TRIGGER IF EXISTS set_users_updated_at ON users;
CREATE TRIGGER set_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_profiles_updated_at ON user_profiles;
CREATE TRIGGER set_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_schemes_updated_at ON schemes;
CREATE TRIGGER set_schemes_updated_at BEFORE UPDATE ON schemes
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_conversations_updated_at ON conversations;
CREATE TRIGGER set_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_documents_updated_at ON documents;
CREATE TRIGGER set_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
