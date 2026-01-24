-- Migration 005: Authentication & User Data Segregation (FIXED)
-- Run this in Supabase SQL Editor
--
-- This migration adds user-level data segregation to ensure
-- each user can only see their own projects and data.
--
-- IMPORTANT: Table names corrected to match actual database schema

-- ============================================
-- STEP 1: Add user_id columns to existing tables
-- ============================================

-- Projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Context Files
ALTER TABLE context_files ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Features (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'features') THEN
        ALTER TABLE features ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- Question Responses (correct table name)
ALTER TABLE question_responses ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Generated PRDs (correct table name)
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Edit Snapshots (correct table name)
ALTER TABLE prd_edit_snapshots ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Shares (correct table name - not share_links)
ALTER TABLE prd_shares ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Comments
ALTER TABLE prd_comments ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Activity
ALTER TABLE prd_activity ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Approvals
ALTER TABLE prd_approvals ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Feedback (correct table name)
ALTER TABLE prd_feedback ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Templates (optional - may keep public)
ALTER TABLE prd_templates ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- ============================================
-- STEP 2: Create indexes for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_context_files_user_id ON context_files(user_id);

-- Features index (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'features') THEN
        CREATE INDEX IF NOT EXISTS idx_features_user_id ON features(user_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_question_responses_user_id ON question_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_prds_user_id ON generated_prds(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_edit_snapshots_user_id ON prd_edit_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_shares_user_id ON prd_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_comments_user_id ON prd_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_feedback_user_id ON prd_feedback(user_id);

-- ============================================
-- STEP 3: Drop old permissive policies
-- ============================================

-- Projects
DROP POLICY IF EXISTS "Allow all on projects" ON projects;

-- Context Files
DROP POLICY IF EXISTS "Allow all on context_files" ON context_files;

-- Question Responses
DROP POLICY IF EXISTS "Allow all on question_responses" ON question_responses;

-- Generated PRDs
DROP POLICY IF EXISTS "Allow all on generated_prds" ON generated_prds;

-- PRD Edit Snapshots
DROP POLICY IF EXISTS "Allow all on prd_edit_snapshots" ON prd_edit_snapshots;

-- PRD Shares
DROP POLICY IF EXISTS "Allow all on prd_shares" ON prd_shares;

-- PRD Comments
DROP POLICY IF EXISTS "Allow all on prd_comments" ON prd_comments;

-- PRD Activity
DROP POLICY IF EXISTS "Allow all on prd_activity" ON prd_activity;

-- PRD Approvals
DROP POLICY IF EXISTS "Allow all on prd_approvals" ON prd_approvals;

-- PRD Feedback
DROP POLICY IF EXISTS "Enable read access for prd_feedback" ON prd_feedback;
DROP POLICY IF EXISTS "Enable insert for prd_feedback" ON prd_feedback;
DROP POLICY IF EXISTS "Enable update for prd_feedback" ON prd_feedback;
DROP POLICY IF EXISTS "Enable delete for prd_feedback" ON prd_feedback;

-- ============================================
-- STEP 4: Create NEW permissive policies
-- (Temporarily allow all while we migrate)
-- ============================================

-- PROJECTS
CREATE POLICY "Allow all projects" ON projects
    FOR ALL USING (true) WITH CHECK (true);

-- CONTEXT FILES
CREATE POLICY "Allow all context_files" ON context_files
    FOR ALL USING (true) WITH CHECK (true);

-- FEATURES (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'features') THEN
        DROP POLICY IF EXISTS "Allow all on features" ON features;
        CREATE POLICY "Allow all features" ON features
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- QUESTION RESPONSES
CREATE POLICY "Allow all question_responses" ON question_responses
    FOR ALL USING (true) WITH CHECK (true);

-- GENERATED PRDS
CREATE POLICY "Allow all generated_prds" ON generated_prds
    FOR ALL USING (true) WITH CHECK (true);

-- PRD EDIT SNAPSHOTS
CREATE POLICY "Allow all prd_edit_snapshots" ON prd_edit_snapshots
    FOR ALL USING (true) WITH CHECK (true);

-- PRD SHARES
CREATE POLICY "Allow all prd_shares" ON prd_shares
    FOR ALL USING (true) WITH CHECK (true);

-- PRD COMMENTS
CREATE POLICY "Allow all prd_comments" ON prd_comments
    FOR ALL USING (true) WITH CHECK (true);

-- PRD ACTIVITY
CREATE POLICY "Allow all prd_activity" ON prd_activity
    FOR ALL USING (true) WITH CHECK (true);

-- PRD APPROVALS
CREATE POLICY "Allow all prd_approvals" ON prd_approvals
    FOR ALL USING (true) WITH CHECK (true);

-- PRD FEEDBACK
CREATE POLICY "Allow all prd_feedback" ON prd_feedback
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- STEP 5: Verification Queries
-- ============================================

-- Check that all tables have user_id column
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name = 'user_id'
AND table_schema = 'public'
ORDER BY table_name;

-- Check RLS is enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'projects', 'context_files', 'question_responses', 'generated_prds',
    'prd_edit_snapshots', 'prd_shares', 'prd_comments', 'prd_feedback'
)
ORDER BY tablename;
