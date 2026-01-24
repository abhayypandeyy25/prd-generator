-- Migration 005: Authentication & User Data Segregation
-- Run this in Supabase SQL Editor
--
-- This migration adds user-level data segregation to ensure
-- each user can only see their own projects and data.

-- ============================================
-- STEP 1: Add user_id columns to all tables
-- ============================================

-- Projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Context Files
ALTER TABLE context_files ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Features
ALTER TABLE features ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Questions Responses
ALTER TABLE questions_responses ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRDs
ALTER TABLE prds ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Snapshots
ALTER TABLE prd_snapshots ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- PRD Comments
ALTER TABLE prd_comments ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Share Links
ALTER TABLE share_links ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Feedback
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- ============================================
-- STEP 2: Create indexes for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_context_files_user_id ON context_files(user_id);
CREATE INDEX IF NOT EXISTS idx_features_user_id ON features(user_id);
CREATE INDEX IF NOT EXISTS idx_questions_responses_user_id ON questions_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_prds_user_id ON prds(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_snapshots_user_id ON prd_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_prd_comments_user_id ON prd_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_share_links_user_id ON share_links(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);

-- ============================================
-- STEP 3: Helper function for RLS
-- ============================================

-- Function to get current user_id from session
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.user_id', true);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 4: Drop old permissive policies
-- ============================================

-- Projects
DROP POLICY IF EXISTS "Allow all on projects" ON projects;

-- Context Files
DROP POLICY IF EXISTS "Allow all on context_files" ON context_files;

-- Features
DROP POLICY IF EXISTS "Allow all on features" ON features;

-- Questions Responses
DROP POLICY IF EXISTS "Allow all on questions_responses" ON questions_responses;

-- PRDs
DROP POLICY IF EXISTS "Allow all on prds" ON prds;

-- PRD Snapshots
DROP POLICY IF EXISTS "Allow all on prd_snapshots" ON prd_snapshots;

-- PRD Comments
DROP POLICY IF EXISTS "Allow all on prd_comments" ON prd_comments;

-- Share Links
DROP POLICY IF EXISTS "Allow all on share_links" ON share_links;

-- Feedback
DROP POLICY IF EXISTS "Allow all on feedback" ON feedback;

-- ============================================
-- STEP 5: Create RLS Policies
-- ============================================

-- PROJECTS
-- --------
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert own projects" ON projects
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (user_id = get_current_user_id());


-- CONTEXT FILES
-- -------------
CREATE POLICY "Users can view own context files" ON context_files
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert own context files" ON context_files
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can delete own context files" ON context_files
    FOR DELETE USING (user_id = get_current_user_id());


-- FEATURES
-- --------
CREATE POLICY "Users can view own features" ON features
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert own features" ON features
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can update own features" ON features
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own features" ON features
    FOR DELETE USING (user_id = get_current_user_id());


-- QUESTIONS RESPONSES
-- -------------------
CREATE POLICY "Users can view own responses" ON questions_responses
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert own responses" ON questions_responses
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can update own responses" ON questions_responses
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own responses" ON questions_responses
    FOR DELETE USING (user_id = get_current_user_id());


-- PRDS
-- ----
CREATE POLICY "Users can view own PRDs" ON prds
    FOR SELECT USING (
        user_id = get_current_user_id()
        OR id IN (
            SELECT prd_id FROM share_links
            WHERE is_active = true
            AND (expires_at IS NULL OR expires_at > NOW())
        )
    );

CREATE POLICY "Users can insert own PRDs" ON prds
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can update own PRDs" ON prds
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own PRDs" ON prds
    FOR DELETE USING (user_id = get_current_user_id());


-- PRD SNAPSHOTS
-- -------------
CREATE POLICY "Users can view own snapshots" ON prd_snapshots
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert own snapshots" ON prd_snapshots
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can delete own snapshots" ON prd_snapshots
    FOR DELETE USING (user_id = get_current_user_id());


-- PRD COMMENTS
-- ------------
CREATE POLICY "Users can view comments on accessible PRDs" ON prd_comments
    FOR SELECT USING (
        user_id = get_current_user_id()
        OR prd_id IN (
            SELECT id FROM prds
            WHERE user_id = get_current_user_id()
            OR id IN (
                SELECT prd_id FROM share_links
                WHERE is_active = true
                AND (expires_at IS NULL OR expires_at > NOW())
            )
        )
    );

CREATE POLICY "Users can insert comments" ON prd_comments
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can update own comments" ON prd_comments
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own comments" ON prd_comments
    FOR DELETE USING (user_id = get_current_user_id());


-- SHARE LINKS
-- -----------
CREATE POLICY "Users can view own share links" ON share_links
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can create share links" ON share_links
    FOR INSERT WITH CHECK (user_id = get_current_user_id());

CREATE POLICY "Users can revoke own share links" ON share_links
    FOR UPDATE USING (user_id = get_current_user_id());

CREATE POLICY "Users can delete own share links" ON share_links
    FOR DELETE USING (user_id = get_current_user_id());


-- FEEDBACK
-- --------
CREATE POLICY "Users can view own feedback" ON feedback
    FOR SELECT USING (user_id = get_current_user_id());

CREATE POLICY "Users can insert feedback" ON feedback
    FOR INSERT WITH CHECK (user_id = get_current_user_id());


-- ============================================
-- STEP 6: Verification Queries
-- ============================================

-- Check that all tables have user_id column
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name = 'user_id'
AND table_schema = 'public'
ORDER BY table_name;

-- Check that all indexes were created
SELECT indexname, tablename
FROM pg_indexes
WHERE indexname LIKE '%user_id%'
AND schemaname = 'public'
ORDER BY tablename;

-- Check RLS is enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'projects', 'context_files', 'features', 'questions_responses',
    'prds', 'prd_snapshots', 'prd_comments', 'share_links', 'feedback'
)
ORDER BY tablename;

-- Count policies per table
SELECT schemaname, tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY schemaname, tablename
ORDER BY tablename;
