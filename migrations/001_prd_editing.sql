-- Migration 001: PRD Editing & Version History
-- Run this in Supabase SQL Editor

-- Add editing metadata to generated_prds table
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMPTZ;
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS is_manually_edited BOOLEAN DEFAULT false;
ALTER TABLE generated_prds ADD COLUMN IF NOT EXISTS original_content_md TEXT;

-- Store edit snapshots for undo/redo and version history
CREATE TABLE IF NOT EXISTS prd_edit_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_content TEXT NOT NULL,
    version_name VARCHAR(255),
    is_major_version BOOLEAN DEFAULT false,
    change_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_prd_snapshots_prd_id ON prd_edit_snapshots(prd_id);
CREATE INDEX IF NOT EXISTS idx_prd_snapshots_project_id ON prd_edit_snapshots(project_id);
CREATE INDEX IF NOT EXISTS idx_prd_snapshots_major ON prd_edit_snapshots(prd_id, is_major_version);

-- Enable RLS
ALTER TABLE prd_edit_snapshots ENABLE ROW LEVEL SECURITY;

-- Create policy for snapshots
CREATE POLICY "Allow all on prd_edit_snapshots" ON prd_edit_snapshots
    FOR ALL USING (true) WITH CHECK (true);

-- Add trigger to auto-update last_edited_at
CREATE OR REPLACE FUNCTION update_prd_edited_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_edited_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prd_edit_timestamp ON generated_prds;
CREATE TRIGGER prd_edit_timestamp
    BEFORE UPDATE ON generated_prds
    FOR EACH ROW
    WHEN (OLD.content_md IS DISTINCT FROM NEW.content_md)
    EXECUTE FUNCTION update_prd_edited_at();
