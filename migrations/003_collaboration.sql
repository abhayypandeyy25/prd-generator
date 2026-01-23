-- Migration 003: Collaboration & Sharing
-- Run this in Supabase SQL Editor

-- Add status to generated_prds for approval workflow
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft';

-- Create sharing links table
CREATE TABLE IF NOT EXISTS prd_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    access_type VARCHAR(50) DEFAULT 'view', -- 'view', 'comment', 'edit'
    password_hash VARCHAR(255),
    expires_at TIMESTAMPTZ,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create comments table
CREATE TABLE IF NOT EXISTS prd_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    section_id VARCHAR(100),
    text_selection TEXT,
    comment_text TEXT NOT NULL,
    parent_comment_id UUID REFERENCES prd_comments(id) ON DELETE CASCADE,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create activity log table
CREATE TABLE IF NOT EXISTS prd_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- 'viewed', 'commented', 'edited', 'shared', 'approved', 'rejected'
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create approvals table
CREATE TABLE IF NOT EXISTS prd_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    approver_name VARCHAR(255) NOT NULL,
    approver_email VARCHAR(255) NOT NULL,
    approval_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    comment TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prd_shares_token ON prd_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_prd_shares_prd ON prd_shares(prd_id);
CREATE INDEX IF NOT EXISTS idx_prd_comments_prd ON prd_comments(prd_id);
CREATE INDEX IF NOT EXISTS idx_prd_comments_parent ON prd_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_prd_activity_prd ON prd_activity(prd_id);
CREATE INDEX IF NOT EXISTS idx_prd_activity_type ON prd_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_prd_approvals_prd ON prd_approvals(prd_id);
CREATE INDEX IF NOT EXISTS idx_prd_approvals_token ON prd_approvals(approval_token);

-- Enable RLS
ALTER TABLE prd_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_approvals ENABLE ROW LEVEL SECURITY;

-- Create permissive policies
CREATE POLICY "Allow all on prd_shares" ON prd_shares
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on prd_comments" ON prd_comments
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on prd_activity" ON prd_activity
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on prd_approvals" ON prd_approvals
    FOR ALL USING (true) WITH CHECK (true);

-- Trigger for comment updated_at
CREATE OR REPLACE FUNCTION update_comment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS comment_updated_at ON prd_comments;
CREATE TRIGGER comment_updated_at
    BEFORE UPDATE ON prd_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_comment_timestamp();
