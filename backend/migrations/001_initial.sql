-- ClassOS V1 — Initial Schema
-- Run against Supabase PostgreSQL (pgvector extension enabled)

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────
-- ORGANISATION HIERARCHY
-- ─────────────────────────────────────────────

CREATE TABLE institutes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    logo_url        TEXT,
    subscription_plan TEXT DEFAULT 'trial',  -- trial | basic | pro | enterprise
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID NOT NULL REFERENCES institutes(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    city            TEXT,
    address         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID NOT NULL REFERENCES institutes(id) ON DELETE CASCADE,
    branch_id       UUID REFERENCES branches(id) ON DELETE SET NULL,
    role            TEXT NOT NULL CHECK (role IN ('platform_admin','institute_admin','branch_admin','teacher')),
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE teacher_assignments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    branch_id       UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    class           INT NOT NULL CHECK (class BETWEEN 1 AND 12),
    section         TEXT,
    subject         TEXT NOT NULL,
    UNIQUE (teacher_id, branch_id, class, section, subject)
);

-- ─────────────────────────────────────────────
-- SUBSCRIPTIONS
-- ─────────────────────────────────────────────

CREATE TABLE institute_subscriptions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID NOT NULL REFERENCES institutes(id) ON DELETE CASCADE,
    board           TEXT NOT NULL,  -- CBSE | Maharashtra SSC
    class           INT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'trial' CHECK (status IN ('active','expired','trial')),
    starts_at       TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    UNIQUE (institute_id, board, class)
);

-- ─────────────────────────────────────────────
-- PUBLISHERS & CONTENT LIBRARY
-- ─────────────────────────────────────────────

CREATE TABLE publishers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL UNIQUE,
    logo_url        TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE books (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publisher_id    UUID NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    subject         TEXT NOT NULL,
    class           INT NOT NULL CHECK (class BETWEEN 1 AND 12),
    board           TEXT NOT NULL,
    edition         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chapters (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id             UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number      INT NOT NULL,
    chapter_name        TEXT NOT NULL,
    content_text        TEXT,
    subtopics           JSONB DEFAULT '[]',
    processing_status   TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending','extracting','chunking','done','failed')),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (book_id, chapter_number)
);

CREATE TABLE chapter_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id      UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    chunk_index     INT NOT NULL,
    content         TEXT NOT NULL,
    page_number     INT,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (chapter_id, chunk_index)
);

CREATE INDEX ON chapter_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─────────────────────────────────────────────
-- QUESTION BANK
-- ─────────────────────────────────────────────

CREATE TABLE questions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type     TEXT NOT NULL CHECK (source_type IN ('publisher_bank','ai_bank','teacher_created')),
    publisher_id    UUID REFERENCES publishers(id),
    book_id         UUID REFERENCES books(id),
    chapter_id      UUID REFERENCES chapters(id),
    subject         TEXT NOT NULL,
    class           INT NOT NULL,
    board           TEXT NOT NULL,
    question_type   TEXT NOT NULL CHECK (question_type IN ('MCQ','VSA','SA','LA','Numerical')),
    marks           INT NOT NULL CHECK (marks IN (1,2,3,4,5,8)),
    difficulty      TEXT NOT NULL CHECK (difficulty IN ('Easy','Medium','Hard')),
    cognitive_level TEXT CHECK (cognitive_level IN ('Knowledge','Understanding','Application','Analysis')),
    language        TEXT DEFAULT 'en' CHECK (language IN ('en','hi','mr','sa','fr')),
    question_text   TEXT NOT NULL,
    options         JSONB,   -- [{key: 'A', text: '...'}] for MCQ
    answer          TEXT NOT NULL,
    solution        TEXT,
    has_media       BOOLEAN DEFAULT FALSE,
    media           JSONB DEFAULT '[]',  -- [{id, type, url, caption, alt_text}]
    concept_tags    TEXT[] DEFAULT '{}',
    usage_count     INT DEFAULT 0,
    is_approved     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON questions (chapter_id, difficulty, question_type, marks);
CREATE INDEX ON questions (class, board, subject);

CREATE TABLE question_usage (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES questions(id),
    paper_id        UUID,   -- FK added after papers table
    institute_id    UUID NOT NULL REFERENCES institutes(id),
    batch_id        TEXT,   -- e.g. "Class 9 A" — for "already asked" detection
    asked_on        TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PAPER TEMPLATES
-- ─────────────────────────────────────────────

CREATE TABLE paper_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID REFERENCES institutes(id) ON DELETE CASCADE,  -- NULL = system default
    name            TEXT NOT NULL,
    total_marks     INT NOT NULL,
    is_system_default BOOLEAN DEFAULT FALSE,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_template_sections (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id         UUID NOT NULL REFERENCES paper_templates(id) ON DELETE CASCADE,
    section_label       TEXT NOT NULL,  -- 'A', 'B', 'C', 'D'
    question_type       TEXT NOT NULL,
    marks_per_question  INT NOT NULL,
    question_count      INT NOT NULL,
    difficulty_mix      JSONB DEFAULT '{"Easy": 30, "Medium": 50, "Hard": 20}',
    sort_order          INT DEFAULT 0
);

-- ─────────────────────────────────────────────
-- PAPERS
-- ─────────────────────────────────────────────

CREATE TABLE papers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID NOT NULL REFERENCES institutes(id),
    branch_id       UUID REFERENCES branches(id),
    created_by      UUID NOT NULL REFERENCES users(id),
    title           TEXT NOT NULL,
    class           INT NOT NULL,
    section         TEXT,
    subject         TEXT NOT NULL,
    board           TEXT NOT NULL,
    publisher_id    UUID REFERENCES publishers(id),
    template_id     UUID REFERENCES paper_templates(id),
    chapter_ids     UUID[] DEFAULT '{}',
    generation_mode TEXT DEFAULT 'bank' CHECK (generation_mode IN ('bank','ai','mixed')),
    language        TEXT DEFAULT 'en',
    bilingual       BOOLEAN DEFAULT FALSE,
    total_marks     INT,
    status          TEXT DEFAULT 'draft' CHECK (status IN ('draft','final')),
    pdf_url         TEXT,
    answer_key_pdf_url TEXT,
    qr_payload      JSONB,
    print_settings  JSONB DEFAULT '{"font_size": 12, "answer_space": 3, "margins": "normal", "numbering": "sequential", "sets": 1}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE paper_questions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id        UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    question_id     UUID NOT NULL REFERENCES questions(id),
    section_label   TEXT NOT NULL,
    question_order  INT NOT NULL,
    marks           INT NOT NULL,
    set_variant     TEXT DEFAULT 'A',  -- 'A' or 'B'
    UNIQUE (paper_id, question_order, set_variant)
);

CREATE TABLE paper_generation_sources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id        UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL CHECK (source_type IN ('chapter_select','subtopic_select','page_range','page_upload','custom_text')),
    chapter_ids     UUID[] DEFAULT '{}',
    subtopic_ids    UUID[] DEFAULT '{}',
    page_ranges     JSONB DEFAULT '[]',  -- [{chapter_id, ranges: "1-10,13-15"}]
    uploaded_file_url TEXT,
    custom_text     TEXT,
    extracted_content TEXT
);

-- Add FK from question_usage to papers now that papers table exists
ALTER TABLE question_usage ADD CONSTRAINT fk_paper FOREIGN KEY (paper_id) REFERENCES papers(id);

-- ─────────────────────────────────────────────
-- CREDITS
-- ─────────────────────────────────────────────

CREATE TABLE institute_credits (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id        UUID NOT NULL UNIQUE REFERENCES institutes(id) ON DELETE CASCADE,
    current_balance     INT DEFAULT 0,
    total_purchased     INT DEFAULT 0,
    total_used          INT DEFAULT 0,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE credit_transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id    UUID NOT NULL REFERENCES institutes(id),
    type            TEXT NOT NULL CHECK (type IN ('purchase','consumed','refund')),
    amount          INT NOT NULL,
    paper_id        UUID REFERENCES papers(id),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- JOBS
-- ─────────────────────────────────────────────

CREATE TABLE pdf_ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id         UUID NOT NULL REFERENCES books(id),
    file_url        TEXT NOT NULL,
    status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','processing','done','failed')),
    pages_processed INT DEFAULT 0,
    total_pages     INT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_generation_jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id        UUID NOT NULL REFERENCES institutes(id),
    paper_id            UUID REFERENCES papers(id),
    chapter_ids         UUID[] DEFAULT '{}',
    requirements        JSONB,
    status              TEXT DEFAULT 'pending' CHECK (status IN ('pending','processing','done','failed')),
    credits_reserved    INT DEFAULT 0,
    credits_consumed    INT DEFAULT 0,
    error_message       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
-- PRINT CONFIG
-- ─────────────────────────────────────────────

CREATE TABLE institute_print_config (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institute_id        UUID NOT NULL UNIQUE REFERENCES institutes(id) ON DELETE CASCADE,
    logo_url            TEXT,
    header_template     JSONB DEFAULT '{"en": ""}',
    default_instructions JSONB DEFAULT '{"en": ""}',
    default_font_size   INT DEFAULT 12,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- ANALYTICS TABLES
-- ─────────────────────────────────────────────

CREATE TABLE question_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES questions(id),
    paper_id        UUID REFERENCES papers(id),
    teacher_id      UUID REFERENCES users(id),
    institute_id    UUID REFERENCES institutes(id),
    branch_id       UUID REFERENCES branches(id),
    event_type      TEXT NOT NULL CHECK (event_type IN ('viewed','added','swapped_out','swapped_in','error_reported','tag_corrected')),
    swap_reason     TEXT CHECK (swap_reason IN ('too_hard','too_easy','already_asked','wrong_topic','poor_quality','other')),
    field_changed   TEXT,
    old_value       TEXT,
    new_value       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE generation_funnel_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      TEXT,
    teacher_id      UUID REFERENCES users(id),
    paper_id        UUID REFERENCES papers(id),
    step            INT NOT NULL CHECK (step BETWEEN 1 AND 7),
    action          TEXT NOT NULL CHECK (action IN ('started','completed','abandoned')),
    time_spent_sec  INT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SEED: System Paper Templates
-- ─────────────────────────────────────────────

INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES
('10 Marks', 10, TRUE),
('20 Marks', 20, TRUE),
('40 Marks', 40, TRUE),
('80 Marks', 80, TRUE);

-- 10-mark template sections
WITH t AS (SELECT id FROM paper_templates WHERE name = '10 Marks' AND is_system_default)
INSERT INTO paper_template_sections (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.section_label, s.question_type, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A', 'MCQ', 1, 5, 1),
  ('B', 'VSA', 1, 3, 2),
  ('C', 'SA',  2, 1, 3)
) AS s(section_label, question_type, mpc, qc, ord);

-- 20-mark template sections
WITH t AS (SELECT id FROM paper_templates WHERE name = '20 Marks' AND is_system_default)
INSERT INTO paper_template_sections (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.section_label, s.question_type, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A', 'MCQ', 1,  5, 1),
  ('B', 'VSA', 2,  3, 2),
  ('C', 'SA',  3,  2, 3),
  ('D', 'LA',  5,  1, 4)
) AS s(section_label, question_type, mpc, qc, ord);

-- 40-mark template sections
WITH t AS (SELECT id FROM paper_templates WHERE name = '40 Marks' AND is_system_default)
INSERT INTO paper_template_sections (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.section_label, s.question_type, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A', 'MCQ', 1,  10, 1),
  ('B', 'VSA', 2,   4, 2),
  ('C', 'SA',  4,   3, 3),
  ('D', 'LA',  5,   2, 4)
) AS s(section_label, question_type, mpc, qc, ord);

-- 80-mark template sections
WITH t AS (SELECT id FROM paper_templates WHERE name = '80 Marks' AND is_system_default)
INSERT INTO paper_template_sections (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.section_label, s.question_type, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A', 'MCQ', 1,  20, 1),
  ('B', 'VSA', 2,   8, 2),
  ('C', 'SA',  3,   4, 3),
  ('D', 'LA',  5,   4, 4),
  ('E', 'LA',  8,   2, 5)
) AS s(section_label, question_type, mpc, qc, ord);

-- ─────────────────────────────────────────────
-- SEED: Publishers
-- ─────────────────────────────────────────────

INSERT INTO publishers (name) VALUES
('Arihant'),
('R.D. Sharma'),
('H.C. Verma'),
('D.C. Pandey'),
('NCERT'),
('S. Chand'),
('Lakhmir Singh'),
('R.S. Aggarwal');
