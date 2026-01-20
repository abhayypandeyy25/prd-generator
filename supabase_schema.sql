-- PM Clarity Supabase Schema
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor > New Query)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Context files table (uploaded documents)
CREATE TABLE IF NOT EXISTS context_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_url TEXT,
    extracted_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Question responses table
CREATE TABLE IF NOT EXISTS question_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    response TEXT,
    ai_suggested BOOLEAN DEFAULT FALSE,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, question_id)
);

-- Generated PRDs table
CREATE TABLE IF NOT EXISTS generated_prds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    content_md TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_context_files_project_id ON context_files(project_id);
CREATE INDEX IF NOT EXISTS idx_question_responses_project_id ON question_responses(project_id);
CREATE INDEX IF NOT EXISTS idx_generated_prds_project_id ON generated_prds(project_id);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_prds ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations with anon key (for development)
-- For production, you'd want more restrictive policies

CREATE POLICY "Allow all on projects" ON projects FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on context_files" ON context_files FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on question_responses" ON question_responses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on generated_prds" ON generated_prds FOR ALL USING (true) WITH CHECK (true);
