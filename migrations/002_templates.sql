-- Migration 002: PRD Templates & Customization
-- Run this in Supabase SQL Editor

-- Create templates table
CREATE TABLE IF NOT EXISTS prd_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create template sections table
CREATE TABLE IF NOT EXISTS template_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prd_templates(id) ON DELETE CASCADE,
    section_name VARCHAR(255) NOT NULL,
    section_order INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT false,
    prompt_template TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create custom questions table
CREATE TABLE IF NOT EXISTS custom_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prd_templates(id) ON DELETE CASCADE,
    section_id VARCHAR(50),
    question_id VARCHAR(50),
    question_text TEXT NOT NULL,
    hint TEXT,
    question_type VARCHAR(50) DEFAULT 'text',
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add template_id to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS template_id UUID REFERENCES prd_templates(id);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_template_sections_template ON template_sections(template_id);
CREATE INDEX IF NOT EXISTS idx_template_sections_order ON template_sections(template_id, section_order);
CREATE INDEX IF NOT EXISTS idx_custom_questions_template ON custom_questions(template_id);
CREATE INDEX IF NOT EXISTS idx_projects_template ON projects(template_id);

-- Enable RLS
ALTER TABLE prd_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_questions ENABLE ROW LEVEL SECURITY;

-- Create permissive policies (adjust as needed for user-based access)
CREATE POLICY "Allow all on prd_templates" ON prd_templates
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on template_sections" ON template_sections
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on custom_questions" ON custom_questions
    FOR ALL USING (true) WITH CHECK (true);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_template_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS template_updated_at ON prd_templates;
CREATE TRIGGER template_updated_at
    BEFORE UPDATE ON prd_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_template_timestamp();

-- Insert default templates

-- 1. Lean PRD (Startup) Template
INSERT INTO prd_templates (id, name, description, is_default, is_public) VALUES
('11111111-1111-1111-1111-111111111111', 'Lean PRD (Startup)', 'A lightweight template focused on speed and clarity. Perfect for startups and MVPs. ~30 questions.', true, true);

INSERT INTO template_sections (template_id, section_name, section_order, is_required, prompt_template) VALUES
('11111111-1111-1111-1111-111111111111', 'Problem Statement', 1, true, 'Describe the core problem being solved and why it matters.'),
('11111111-1111-1111-1111-111111111111', 'Proposed Solution', 2, true, 'Outline the solution approach and key features.'),
('11111111-1111-1111-1111-111111111111', 'Success Metrics', 3, true, 'Define measurable success criteria and KPIs.'),
('11111111-1111-1111-1111-111111111111', 'MVP Features', 4, true, 'List the minimum set of features for initial release.'),
('11111111-1111-1111-1111-111111111111', 'Timeline', 5, false, 'Provide estimated timeline and key milestones.');

-- 2. Detailed PRD (Enterprise) Template
INSERT INTO prd_templates (id, name, description, is_default, is_public) VALUES
('22222222-2222-2222-2222-222222222222', 'Detailed PRD (Enterprise)', 'Comprehensive template for enterprise products. Includes compliance and risk assessment. ~139 questions.', false, true);

INSERT INTO template_sections (template_id, section_name, section_order, is_required, prompt_template) VALUES
('22222222-2222-2222-2222-222222222222', 'Executive Summary', 1, true, 'High-level overview of the product and its business value.'),
('22222222-2222-2222-2222-222222222222', 'Problem Statement', 2, true, 'Detailed problem analysis with market context.'),
('22222222-2222-2222-2222-222222222222', 'Target Users', 3, true, 'User personas, segments, and use cases.'),
('22222222-2222-2222-2222-222222222222', 'Proposed Solution', 4, true, 'Comprehensive solution description.'),
('22222222-2222-2222-2222-222222222222', 'Feature Requirements', 5, true, 'Detailed feature specifications with acceptance criteria.'),
('22222222-2222-2222-2222-222222222222', 'Technical Requirements', 6, true, 'Architecture, integrations, and technical constraints.'),
('22222222-2222-2222-2222-222222222222', 'Success Metrics', 7, true, 'KPIs, OKRs, and measurement strategy.'),
('22222222-2222-2222-2222-222222222222', 'Compliance & Security', 8, true, 'Regulatory requirements and security considerations.'),
('22222222-2222-2222-2222-222222222222', 'Risk Assessment', 9, true, 'Identify risks and mitigation strategies.'),
('22222222-2222-2222-2222-222222222222', 'Timeline & Milestones', 10, true, 'Detailed project timeline with dependencies.'),
('22222222-2222-2222-2222-222222222222', 'Rollout Plan', 11, false, 'Phased rollout strategy and go-live plan.');

-- 3. Technical Spec Template
INSERT INTO prd_templates (id, name, description, is_default, is_public) VALUES
('33333333-3333-3333-3333-333333333333', 'Technical Spec (Engineering)', 'Engineering-focused template with emphasis on architecture and implementation details. ~60 questions.', false, true);

INSERT INTO template_sections (template_id, section_name, section_order, is_required, prompt_template) VALUES
('33333333-3333-3333-3333-333333333333', 'Overview', 1, true, 'Brief overview of the technical problem and solution.'),
('33333333-3333-3333-3333-333333333333', 'System Architecture', 2, true, 'High-level and detailed architecture diagrams and descriptions.'),
('33333333-3333-3333-3333-333333333333', 'API Design', 3, true, 'API endpoints, request/response formats, authentication.'),
('33333333-3333-3333-3333-333333333333', 'Data Models', 4, true, 'Database schema, data flows, and storage considerations.'),
('33333333-3333-3333-3333-333333333333', 'Performance Requirements', 5, true, 'Latency, throughput, scalability requirements.'),
('33333333-3333-3333-3333-333333333333', 'Security Considerations', 6, true, 'Authentication, authorization, data protection.'),
('33333333-3333-3333-3333-333333333333', 'Integration Points', 7, false, 'Third-party services and internal system integrations.'),
('33333333-3333-3333-3333-333333333333', 'Testing Strategy', 8, false, 'Unit, integration, and end-to-end testing approach.');

-- 4. One-Pager (Executive) Template
INSERT INTO prd_templates (id, name, description, is_default, is_public) VALUES
('44444444-4444-4444-4444-444444444444', 'One-Pager (Executive)', 'High-level strategic overview for executive stakeholders. ~15 questions.', false, true);

INSERT INTO template_sections (template_id, section_name, section_order, is_required, prompt_template) VALUES
('44444444-4444-4444-4444-444444444444', 'Vision', 1, true, 'The long-term vision and strategic importance.'),
('44444444-4444-4444-4444-444444444444', 'Problem', 2, true, 'The business problem in 2-3 sentences.'),
('44444444-4444-4444-4444-444444444444', 'Solution', 3, true, 'The proposed solution in 2-3 sentences.'),
('44444444-4444-4444-4444-444444444444', 'Success Metrics', 4, true, 'Key metrics for success.'),
('44444444-4444-4444-4444-444444444444', 'Investment & Timeline', 5, false, 'Required resources and expected timeline.');

-- 5. Feature Brief Template
INSERT INTO prd_templates (id, name, description, is_default, is_public) VALUES
('55555555-5555-5555-5555-555555555555', 'Feature Brief', 'Lightweight template for small features and improvements. ~25 questions.', false, true);

INSERT INTO template_sections (template_id, section_name, section_order, is_required, prompt_template) VALUES
('55555555-5555-5555-5555-555555555555', 'Problem', 1, true, 'What problem does this feature solve?'),
('55555555-5555-5555-5555-555555555555', 'Solution', 2, true, 'How does this feature solve the problem?'),
('55555555-5555-5555-5555-555555555555', 'User Stories', 3, true, 'User stories describing the feature from user perspective.'),
('55555555-5555-5555-5555-555555555555', 'Acceptance Criteria', 4, true, 'Clear, testable acceptance criteria.'),
('55555555-5555-5555-5555-555555555555', 'Out of Scope', 5, false, 'What is explicitly not included in this feature.');
