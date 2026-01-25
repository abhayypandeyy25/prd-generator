-- Migration 005: Authentication & User Data Segregation (SAFE VERSION)
-- Run this in Supabase SQL Editor
--
-- This migration SAFELY adds user_id columns only to tables that exist.
-- It will NOT fail if some tables are missing.

-- ============================================
-- STEP 1: Add user_id columns (SAFE - only if table exists)
-- ============================================

-- Projects (core table - should always exist)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Context Files (core table)
ALTER TABLE context_files ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Question Responses (core table)
ALTER TABLE question_responses ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Generated PRDs (core table)
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Features (may or may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'features') THEN
        ALTER TABLE features ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Edit Snapshots (from migration 001 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_edit_snapshots') THEN
        ALTER TABLE prd_edit_snapshots ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Templates (from migration 002 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_templates') THEN
        ALTER TABLE prd_templates ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Shares (from migration 003 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_shares') THEN
        ALTER TABLE prd_shares ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Comments (from migration 003 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_comments') THEN
        ALTER TABLE prd_comments ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Activity (from migration 003 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_activity') THEN
        ALTER TABLE prd_activity ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Approvals (from migration 003 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_approvals') THEN
        ALTER TABLE prd_approvals ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- PRD Feedback (from migration 004 - may not exist)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_feedback') THEN
        ALTER TABLE prd_feedback ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
    END IF;
END $$;

-- ============================================
-- STEP 2: Create indexes (SAFE)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_context_files_user_id ON context_files(user_id);
CREATE INDEX IF NOT EXISTS idx_question_responses_user_id ON question_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_prds_user_id ON generated_prds(user_id);

-- Optional table indexes
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'features') THEN
        CREATE INDEX IF NOT EXISTS idx_features_user_id ON features(user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_edit_snapshots') THEN
        CREATE INDEX IF NOT EXISTS idx_prd_edit_snapshots_user_id ON prd_edit_snapshots(user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_shares') THEN
        CREATE INDEX IF NOT EXISTS idx_prd_shares_user_id ON prd_shares(user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_comments') THEN
        CREATE INDEX IF NOT EXISTS idx_prd_comments_user_id ON prd_comments(user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_feedback') THEN
        CREATE INDEX IF NOT EXISTS idx_prd_feedback_user_id ON prd_feedback(user_id);
    END IF;
END $$;

-- ============================================
-- STEP 3: Update RLS Policies (SAFE)
-- ============================================

-- Drop and recreate policies for CORE tables only

-- Projects
DROP POLICY IF EXISTS "Allow all on projects" ON projects;
CREATE POLICY "Allow all projects" ON projects FOR ALL USING (true) WITH CHECK (true);

-- Context Files
DROP POLICY IF EXISTS "Allow all on context_files" ON context_files;
CREATE POLICY "Allow all context_files" ON context_files FOR ALL USING (true) WITH CHECK (true);

-- Question Responses
DROP POLICY IF EXISTS "Allow all on question_responses" ON question_responses;
CREATE POLICY "Allow all question_responses" ON question_responses FOR ALL USING (true) WITH CHECK (true);

-- Generated PRDs
DROP POLICY IF EXISTS "Allow all on generated_prds" ON generated_prds;
CREATE POLICY "Allow all generated_prds" ON generated_prds FOR ALL USING (true) WITH CHECK (true);

-- Optional tables (with IF EXISTS)
DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'features') THEN
        DROP POLICY IF EXISTS "Allow all on features" ON features;
        CREATE POLICY "Allow all features" ON features FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_edit_snapshots') THEN
        DROP POLICY IF EXISTS "Allow all on prd_edit_snapshots" ON prd_edit_snapshots;
        CREATE POLICY "Allow all prd_edit_snapshots" ON prd_edit_snapshots FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_templates') THEN
        DROP POLICY IF EXISTS "Allow all on prd_templates" ON prd_templates;
        CREATE POLICY "Allow all prd_templates" ON prd_templates FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_shares') THEN
        DROP POLICY IF EXISTS "Allow all on prd_shares" ON prd_shares;
        CREATE POLICY "Allow all prd_shares" ON prd_shares FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_comments') THEN
        DROP POLICY IF EXISTS "Allow all on prd_comments" ON prd_comments;
        CREATE POLICY "Allow all prd_comments" ON prd_comments FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_activity') THEN
        DROP POLICY IF EXISTS "Allow all on prd_activity" ON prd_activity;
        CREATE POLICY "Allow all prd_activity" ON prd_activity FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_approvals') THEN
        DROP POLICY IF EXISTS "Allow all on prd_approvals" ON prd_approvals;
        CREATE POLICY "Allow all prd_approvals" ON prd_approvals FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'prd_feedback') THEN
        DROP POLICY IF EXISTS "Enable read access for prd_feedback" ON prd_feedback;
        DROP POLICY IF EXISTS "Enable insert for prd_feedback" ON prd_feedback;
        DROP POLICY IF EXISTS "Enable update for prd_feedback" ON prd_feedback;
        DROP POLICY IF EXISTS "Enable delete for prd_feedback" ON prd_feedback;
        CREATE POLICY "Allow all prd_feedback" ON prd_feedback FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ============================================
-- STEP 4: Verification
-- ============================================

-- Show which tables got user_id column
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'user_id'
AND table_schema = 'public'
ORDER BY table_name;

-- Show all tables in your database
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
