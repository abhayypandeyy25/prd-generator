-- PRD Feedback table for AI improvement loop
CREATE TABLE IF NOT EXISTS prd_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('prd_rating', 'question_response', 'section_rating', 'general')),
    question_id TEXT,
    section_name TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_prd_feedback_project ON prd_feedback(project_id);
CREATE INDEX IF NOT EXISTS idx_prd_feedback_type ON prd_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_prd_feedback_question ON prd_feedback(question_id) WHERE question_id IS NOT NULL;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_prd_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prd_feedback_updated_at ON prd_feedback;
CREATE TRIGGER prd_feedback_updated_at
    BEFORE UPDATE ON prd_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_prd_feedback_updated_at();

-- Enable RLS
ALTER TABLE prd_feedback ENABLE ROW LEVEL SECURITY;

-- RLS policies for prd_feedback
DROP POLICY IF EXISTS "Enable read access for prd_feedback" ON prd_feedback;
CREATE POLICY "Enable read access for prd_feedback" ON prd_feedback
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Enable insert for prd_feedback" ON prd_feedback;
CREATE POLICY "Enable insert for prd_feedback" ON prd_feedback
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Enable update for prd_feedback" ON prd_feedback;
CREATE POLICY "Enable update for prd_feedback" ON prd_feedback
    FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Enable delete for prd_feedback" ON prd_feedback;
CREATE POLICY "Enable delete for prd_feedback" ON prd_feedback
    FOR DELETE USING (true);
