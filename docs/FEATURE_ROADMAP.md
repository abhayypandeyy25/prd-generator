# PM Clarity - Feature Roadmap & Implementation Plan

## Overview

This document outlines the implementation plan for the next phase of PM Clarity features, focusing on editing, customization, collaboration, and intelligence.

---

## Feature 1: PRD Editing & Refinement

### Problem Statement
After AI generates the PRD, PMs need to refine, edit, and polish the content. Currently, users can only regenerate the entire PRD or export it—there's no in-app editing capability.

### User Stories
1. "After generating the PRD, I want to fix typos and adjust tone without regenerating everything."
2. "I want to add a section that the AI missed based on my domain knowledge."
3. "I want to see my changes highlighted so I know what I edited vs what AI generated."
4. "I want to undo my last 3 edits without losing the entire PRD."

### Technical Design

#### Database Changes
```sql
-- Add editing metadata to generated_prds table
ALTER TABLE generated_prds ADD COLUMN edit_history JSONB DEFAULT '[]';
ALTER TABLE generated_prds ADD COLUMN last_edited_at TIMESTAMP;
ALTER TABLE generated_prds ADD COLUMN is_manually_edited BOOLEAN DEFAULT false;

-- Store edit snapshots for undo/redo
CREATE TABLE prd_edit_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    snapshot_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    edit_description TEXT
);

CREATE INDEX idx_prd_snapshots_prd_id ON prd_edit_snapshots(prd_id);
```

#### API Endpoints

**1. Update PRD Content**
```
PUT /api/prd/edit/{project_id}
Body: {
  "content": "updated markdown content",
  "description": "Fixed typos in Overview section"
}
Response: { "success": true, "snapshot_id": "..." }
```

**2. Get Edit History**
```
GET /api/prd/history/{project_id}
Response: {
  "snapshots": [
    { "id": "...", "created_at": "...", "description": "..." }
  ]
}
```

**3. Restore Snapshot**
```
POST /api/prd/restore/{project_id}/{snapshot_id}
Response: { "content": "restored markdown" }
```

**4. Regenerate Single Section**
```
POST /api/prd/regenerate-section/{project_id}
Body: { "section_name": "Technical Requirements" }
Response: { "updated_content": "..." }
```

#### Frontend Components

**1. PRD Editor Component** (`components/PRDEditor.vue`)
```vue
<template>
  <div class="prd-editor">
    <!-- Toolbar -->
    <div class="editor-toolbar">
      <button @click="undo" :disabled="!canUndo">↶ Undo</button>
      <button @click="redo" :disabled="!canRedo">↷ Redo</button>
      <button @click="showDiff">👁 View Changes</button>
      <button @click="saveEdit">💾 Save</button>
      <button @click="regenerateSection">✨ Regenerate Section</button>
    </div>

    <!-- Split View: Editor + Preview -->
    <div class="editor-split">
      <!-- Left: Markdown Editor -->
      <div class="editor-pane">
        <textarea
          v-model="editableContent"
          @input="handleEdit"
          class="markdown-editor"
        />
      </div>

      <!-- Right: Live Preview -->
      <div class="preview-pane" v-html="renderedPreview" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()
const editableContent = ref(store.prd || '')
const editHistory = ref([])
const historyIndex = ref(-1)

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < editHistory.value.length - 1)
const renderedPreview = computed(() => marked(editableContent.value))

// Implementation details...
</script>
```

**2. Section Selector Modal**
- Allow users to select which section to regenerate
- Show section list: Overview, Goals, Features, Technical Requirements, etc.
- AI regenerates only that section

**3. Diff Viewer**
- Show original AI-generated content vs edited content
- Highlight additions in green, deletions in red
- Use `diff-match-patch` library

#### Implementation Steps
1. ✅ **Week 1:** Database schema updates, migration scripts
2. ✅ **Week 1:** API endpoints for edit, history, restore
3. ✅ **Week 2:** Frontend editor component with split view
4. ✅ **Week 2:** Undo/redo functionality with history snapshots
5. ✅ **Week 3:** Section regeneration feature
6. ✅ **Week 3:** Diff viewer and change tracking
7. ✅ **Week 4:** Testing, polish, documentation

---

## Feature 2: PRD Templates & Customization

### Problem Statement
Different teams/companies use different PRD formats. The current 139-question structure doesn't fit everyone's workflow. Some need lean PRDs, others need detailed technical specs.

### User Stories
1. "My company uses a specific PRD format. I want to customize sections to match our template."
2. "I only need 5 core sections, not 15. I want to hide irrelevant sections."
3. "I want to save my custom template and reuse it for all my projects."
4. "I want to add custom questions specific to my industry (e.g., healthcare compliance)."

### Technical Design

#### Database Changes
```sql
-- Templates table
CREATE TABLE prd_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false, -- For community templates
    created_by VARCHAR(255), -- Future: user_id when auth added
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Template sections (defines structure)
CREATE TABLE template_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prd_templates(id) ON DELETE CASCADE,
    section_name VARCHAR(255) NOT NULL,
    section_order INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT false,
    prompt_template TEXT, -- AI prompt for generating this section
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_template_sections_template ON template_sections(template_id);

-- Custom questions (extends questions.json)
CREATE TABLE custom_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prd_templates(id) ON DELETE CASCADE,
    section_id VARCHAR(50), -- e.g., "1.1"
    question_id VARCHAR(50), -- e.g., "1.1.8"
    question_text TEXT NOT NULL,
    hint TEXT,
    question_type VARCHAR(50) DEFAULT 'text',
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Link projects to templates
ALTER TABLE projects ADD COLUMN template_id UUID REFERENCES prd_templates(id);
```

#### Built-in Templates

**1. Lean PRD (Startup)**
- Sections: Problem, Solution, Success Metrics, MVP Features, Timeline
- ~30 questions
- Focus: Speed, clarity, actionable

**2. Detailed PRD (Enterprise)**
- All current sections + Compliance, Risk Assessment, Rollout Plan
- ~139 questions (current default)
- Focus: Comprehensive, audit-ready

**3. Technical Spec (Engineering-Heavy)**
- Sections: Architecture, APIs, Data Models, Performance, Security
- ~60 questions
- Focus: Technical depth

**4. One-Pager (Executive)**
- Sections: Vision, Problem, Solution, Success Metrics
- ~15 questions
- Focus: High-level, strategic

**5. Feature Brief (Small Feature)**
- Sections: Problem, Solution, User Stories, Acceptance Criteria
- ~25 questions
- Focus: Lightweight, fast

#### API Endpoints

**1. List Templates**
```
GET /api/templates
Response: {
  "templates": [
    { "id": "...", "name": "Lean PRD", "description": "...", "is_default": true },
    { "id": "...", "name": "Technical Spec", "description": "..." }
  ]
}
```

**2. Get Template Details**
```
GET /api/templates/{template_id}
Response: {
  "template": { ... },
  "sections": [ ... ],
  "custom_questions": [ ... ]
}
```

**3. Create Custom Template**
```
POST /api/templates
Body: {
  "name": "My Company PRD",
  "description": "Our standard format",
  "sections": [
    { "name": "Business Case", "order": 1, "required": true },
    { "name": "User Stories", "order": 2, "required": true }
  ]
}
```

**4. Apply Template to Project**
```
POST /api/projects/{project_id}/apply-template
Body: { "template_id": "..." }
Response: { "success": true }
```

**5. Clone & Customize Template**
```
POST /api/templates/{template_id}/clone
Body: { "new_name": "My Custom Template" }
Response: { "new_template_id": "..." }
```

#### Frontend Components

**1. Template Selector** (`components/TemplateSelector.vue`)
```vue
<template>
  <div class="template-selector">
    <h3>Choose PRD Template</h3>
    <div class="template-grid">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        :class="{ selected: selectedTemplate === template.id }"
        @click="selectTemplate(template.id)"
      >
        <h4>{{ template.name }}</h4>
        <p>{{ template.description }}</p>
        <span class="question-count">{{ template.question_count }} questions</span>
      </div>
    </div>
  </div>
</template>
```

**2. Template Editor** (`components/TemplateEditor.vue`)
- Drag-and-drop section reordering
- Add/remove sections
- Toggle required sections
- Add custom questions
- Save as new template

**3. Project Setup Wizard**
- Step 1: Choose template
- Step 2: Upload context
- Step 3: Proceed to features

#### Implementation Steps
1. ✅ **Week 1:** Database schema, seed default templates
2. ✅ **Week 2:** Template CRUD API endpoints
3. ✅ **Week 2:** Template selector UI in project creation
4. ✅ **Week 3:** Template editor for customization
5. ✅ **Week 3:** Dynamic question loading based on template
6. ✅ **Week 4:** PRD generation adapted to template structure
7. ✅ **Week 4:** Testing, documentation

---

## Feature 3: Collaboration & Sharing

### Problem Statement
PRDs are team documents. Currently, PM Clarity is single-user. PMs need to share drafts, collect feedback, and approve with stakeholders.

### User Stories
1. "I want to share my draft PRD with my engineering lead via a link."
2. "I want to see comments from reviewers on specific sections."
3. "I want to track who viewed my PRD and when."
4. "I want an approval workflow: draft → review → approved."

### Technical Design

#### Database Changes
```sql
-- Sharing links
CREATE TABLE prd_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    access_type VARCHAR(50) DEFAULT 'view', -- view, comment, edit
    password_hash VARCHAR(255), -- Optional password protection
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    view_count INTEGER DEFAULT 0
);

CREATE INDEX idx_prd_shares_token ON prd_shares(share_token);
CREATE INDEX idx_prd_shares_prd ON prd_shares(prd_id);

-- Comments
CREATE TABLE prd_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    section_id VARCHAR(100), -- Which section (e.g., "Overview", "Features")
    text_selection TEXT, -- Specific text being commented on
    comment_text TEXT NOT NULL,
    parent_comment_id UUID REFERENCES prd_comments(id), -- For replies
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prd_comments_prd ON prd_comments(prd_id);

-- Activity log
CREATE TABLE prd_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    activity_type VARCHAR(50), -- viewed, commented, edited, approved
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prd_activity_prd ON prd_activity(prd_id);

-- Approval workflow
ALTER TABLE generated_prds ADD COLUMN status VARCHAR(50) DEFAULT 'draft';
-- Status: draft, in_review, approved, archived

CREATE TABLE prd_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prd_id UUID REFERENCES generated_prds(id) ON DELETE CASCADE,
    approver_name VARCHAR(255) NOT NULL,
    approver_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    comment TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### API Endpoints

**1. Create Share Link**
```
POST /api/prd/share/{project_id}
Body: {
  "access_type": "comment",
  "password": "optional-password",
  "expires_in_days": 7
}
Response: {
  "share_url": "https://pm-clarity.vercel.app/shared/abc123xyz",
  "token": "abc123xyz"
}
```

**2. Access Shared PRD**
```
GET /api/prd/shared/{share_token}
Query: ?password=xyz (if password-protected)
Response: {
  "prd": { ... },
  "access_type": "comment",
  "can_comment": true,
  "can_edit": false
}
```

**3. Add Comment**
```
POST /api/prd/comments/{prd_id}
Body: {
  "author_name": "Alice",
  "author_email": "alice@example.com",
  "section_id": "Overview",
  "text_selection": "specific text",
  "comment_text": "Should we clarify this?"
}
```

**4. Get Comments**
```
GET /api/prd/comments/{prd_id}
Response: {
  "comments": [
    { "id": "...", "author": "...", "text": "...", "created_at": "..." }
  ]
}
```

**5. Resolve Comment**
```
POST /api/prd/comments/{comment_id}/resolve
Response: { "success": true }
```

**6. Request Approval**
```
POST /api/prd/request-approval/{project_id}
Body: {
  "approvers": [
    { "name": "CTO", "email": "cto@company.com" },
    { "name": "VP Product", "email": "vp@company.com" }
  ]
}
Response: { "approval_requests_sent": 2 }
```

**7. Approve/Reject PRD**
```
POST /api/prd/approve/{prd_id}/{approval_token}
Body: { "status": "approved", "comment": "LGTM!" }
```

**8. Get Activity Log**
```
GET /api/prd/activity/{prd_id}
Response: {
  "activities": [
    { "type": "viewed", "actor": "alice@company.com", "timestamp": "..." },
    { "type": "commented", "actor": "bob@company.com", "timestamp": "..." }
  ]
}
```

#### Frontend Components

**1. Share Modal** (`components/ShareModal.vue`)
```vue
<template>
  <div class="modal-overlay">
    <div class="modal share-modal">
      <h3>Share PRD</h3>

      <!-- Access Type -->
      <div class="form-group">
        <label>Access Level</label>
        <select v-model="accessType">
          <option value="view">View Only</option>
          <option value="comment">View & Comment</option>
          <option value="edit">View & Edit</option>
        </select>
      </div>

      <!-- Optional Password -->
      <div class="form-group">
        <label>Password (optional)</label>
        <input type="password" v-model="password" placeholder="Leave empty for no password" />
      </div>

      <!-- Expiry -->
      <div class="form-group">
        <label>Expires In</label>
        <select v-model="expiresInDays">
          <option :value="1">1 day</option>
          <option :value="7">7 days</option>
          <option :value="30">30 days</option>
          <option :value="null">Never</option>
        </select>
      </div>

      <!-- Generated Link -->
      <div v-if="shareLink" class="share-link">
        <input :value="shareLink" readonly />
        <button @click="copyLink">📋 Copy</button>
      </div>

      <div class="modal-actions">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button class="btn btn-primary" @click="generateLink">Generate Link</button>
      </div>
    </div>
  </div>
</template>
```

**2. Comments Sidebar** (`components/CommentsSidebar.vue`)
- Show all comments grouped by section
- Reply to comments
- Mark as resolved
- Real-time updates (optional: WebSocket)

**3. Shared PRD View** (`views/SharedPRDView.vue`)
- Read-only or editable based on access_type
- Comment highlighting on text selection
- Password prompt if protected
- Track view in activity log

**4. Activity Timeline** (`components/ActivityTimeline.vue`)
- Show who viewed, when
- Show who commented, when
- Show edits, approvals

**5. Approval Workflow** (`components/ApprovalWidget.vue`)
- Request approval from stakeholders
- Show approval status (pending/approved/rejected)
- Display approval comments

#### Implementation Steps
1. ✅ **Week 1:** Database schema for sharing, comments, activity
2. ✅ **Week 2:** API endpoints for sharing and comments
3. ✅ **Week 2:** Share modal and link generation UI
4. ✅ **Week 3:** Shared PRD view (public access)
5. ✅ **Week 3:** Comments sidebar and threading
6. ✅ **Week 4:** Activity log and approval workflow
7. ✅ **Week 4:** Email notifications (optional)
8. ✅ **Week 5:** Testing, security review

---

## Feature 4: Version History & Comparison

### Problem Statement
PRDs evolve through multiple iterations. PMs need to track what changed between versions, restore previous versions, and show stakeholders the delta.

### User Stories
1. "I made changes after the meeting. I want to compare before/after to generate a changelog."
2. "I accidentally deleted a section. I want to restore v3 without losing v4."
3. "I want to show my manager exactly what changed since last week's review."
4. "I want to name versions (v1.0 Initial, v2.0 Post-Review) for clarity."

### Technical Design

#### Database Changes
```sql
-- Already have prd_edit_snapshots from Feature 1
-- Enhance it with versioning

ALTER TABLE prd_edit_snapshots ADD COLUMN version_name VARCHAR(255);
ALTER TABLE prd_edit_snapshots ADD COLUMN is_major_version BOOLEAN DEFAULT false;
ALTER TABLE prd_edit_snapshots ADD COLUMN change_summary TEXT;

-- Index for efficient version queries
CREATE INDEX idx_snapshots_major_versions ON prd_edit_snapshots(prd_id, is_major_version);
```

#### API Endpoints

**1. List Versions**
```
GET /api/prd/versions/{project_id}
Response: {
  "versions": [
    {
      "id": "...",
      "version_name": "v2.0 - Post-Review",
      "created_at": "...",
      "change_summary": "Updated success metrics",
      "is_major": true
    },
    {
      "id": "...",
      "version_name": "v1.0 - Initial Draft",
      "created_at": "...",
      "is_major": true
    }
  ],
  "auto_saves": [ ... ] // Auto-saved versions
}
```

**2. Create Named Version**
```
POST /api/prd/versions/{project_id}
Body: {
  "version_name": "v1.5 - Engineering Feedback",
  "change_summary": "Added API endpoints section",
  "is_major": true
}
```

**3. Compare Versions**
```
GET /api/prd/compare/{project_id}?from={version_id_1}&to={version_id_2}
Response: {
  "diff": {
    "additions": [...],
    "deletions": [...],
    "changes": [...]
  },
  "summary": {
    "lines_added": 45,
    "lines_removed": 12,
    "sections_changed": ["Overview", "Success Metrics"]
  }
}
```

**4. Restore Version**
```
POST /api/prd/restore/{project_id}/{version_id}
Body: { "create_backup": true } // Creates snapshot of current before restoring
Response: { "success": true, "backup_id": "..." }
```

**5. Generate Changelog**
```
POST /api/prd/changelog/{project_id}
Body: {
  "from_version": "v1.0",
  "to_version": "v2.0"
}
Response: {
  "changelog_md": "## Changes\n\n### Added\n- Success metrics section\n\n### Modified\n- Updated timeline\n\n### Removed\n- Old assumptions"
}
```

#### Frontend Components

**1. Version History Panel** (`components/VersionHistory.vue`)
```vue
<template>
  <div class="version-history">
    <div class="version-header">
      <h3>Version History</h3>
      <button @click="createVersion" class="btn btn-primary">
        📌 Create Version
      </button>
    </div>

    <!-- Version Timeline -->
    <div class="version-timeline">
      <div
        v-for="version in versions"
        :key="version.id"
        class="version-item"
        :class="{ major: version.is_major }"
      >
        <div class="version-badge">
          {{ version.version_name || 'Auto-save' }}
        </div>
        <div class="version-info">
          <p class="version-time">{{ formatTime(version.created_at) }}</p>
          <p class="version-summary">{{ version.change_summary }}</p>
        </div>
        <div class="version-actions">
          <button @click="viewVersion(version.id)">👁 View</button>
          <button @click="compareVersion(version.id)">⚖️ Compare</button>
          <button @click="restoreVersion(version.id)">↶ Restore</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**2. Version Comparison View** (`components/VersionCompare.vue`)
- Side-by-side diff view
- Unified diff view
- Syntax highlighting for markdown
- Export changelog as markdown

**3. Create Version Modal**
- Name the version
- Add change summary
- Mark as major version

**4. Restore Confirmation Modal**
- Show what will be restored
- Option to backup current version first
- Undo restore option

#### Implementation Steps
1. ✅ **Week 1:** Enhance snapshot schema with versioning
2. ✅ **Week 1:** API endpoints for versioning and comparison
3. ✅ **Week 2:** Version history panel UI
4. ✅ **Week 2:** Version comparison view with diff
5. ✅ **Week 3:** Restore version functionality
6. ✅ **Week 3:** Changelog generation
7. ✅ **Week 4:** Auto-save versions on significant edits
8. ✅ **Week 4:** Testing, polish

---

## Feature 5: Smart Context Analysis

### Problem Statement
Users upload documents blindly. They don't know if they have enough context, what's missing, or if there are contradictions. Help PMs understand their context quality before generating.

### User Stories
1. "I uploaded 5 documents. I want a summary of what's in them before running AI."
2. "I want to know if I'm missing key information like user personas or success metrics."
3. "I want to see if two documents contradict each other on priorities."
4. "I want a 'context quality score' to know if I'm ready to generate."

### Technical Design

#### API Endpoints

**1. Analyze Context**
```
POST /api/context/analyze/{project_id}
Response: {
  "quality_score": 75, // 0-100
  "summary": {
    "total_docs": 5,
    "total_words": 12500,
    "key_themes": ["Mobile app", "User onboarding", "Analytics"],
    "stakeholders_mentioned": ["CEO", "Engineering Lead"],
    "dates_mentioned": ["Q2 2026", "March launch"]
  },
  "coverage": {
    "has_user_personas": true,
    "has_success_metrics": false,
    "has_technical_requirements": true,
    "has_timeline": true,
    "has_competitors": false
  },
  "issues": [
    {
      "type": "missing_info",
      "severity": "medium",
      "message": "No success metrics found. Consider adding KPIs."
    },
    {
      "type": "contradiction",
      "severity": "high",
      "message": "Doc 1 mentions Q2 launch, Doc 3 mentions Q3 launch",
      "sources": ["file1.pdf", "file3.txt"]
    }
  ],
  "suggestions": [
    "Upload a document with success metrics and KPIs",
    "Clarify the launch timeline across documents",
    "Add competitor analysis"
  ]
}
```

**2. Get Document Summary**
```
POST /api/context/summarize/{file_id}
Response: {
  "summary": "This document outlines the mobile app features...",
  "key_points": [
    "Focus on user onboarding",
    "Target iOS first, Android later",
    "Integration with existing backend"
  ],
  "extracted_entities": {
    "people": ["John (CEO)", "Sarah (Designer)"],
    "dates": ["March 2026"],
    "metrics": ["50k users in Q1"]
  }
}
```

**3. Detect Duplicates/Conflicts**
```
GET /api/context/conflicts/{project_id}
Response: {
  "duplicates": [
    {
      "files": ["requirements_v1.pdf", "requirements_v2.pdf"],
      "similarity": 0.95,
      "suggestion": "These files are very similar. Consider keeping only the latest version."
    }
  ],
  "conflicts": [
    {
      "topic": "Launch date",
      "conflicting_statements": [
        { "file": "roadmap.pdf", "text": "Launch in Q2" },
        { "file": "email_thread.txt", "text": "Launch pushed to Q3" }
      ]
    }
  ]
}
```

#### Context Quality Scoring Algorithm

```python
def calculate_quality_score(project_id):
    score = 0
    context_text = get_aggregated_context(project_id)

    # Base score: Content length (max 20 points)
    word_count = len(context_text.split())
    if word_count > 5000:
        score += 20
    elif word_count > 2000:
        score += 15
    elif word_count > 500:
        score += 10

    # Coverage checks (10 points each)
    coverage_checks = [
        ("user personas", ["user", "persona", "target audience"]),
        ("success metrics", ["metric", "KPI", "success criteria", "measure"]),
        ("technical requirements", ["API", "database", "architecture", "tech stack"]),
        ("timeline", ["timeline", "roadmap", "Q1", "Q2", "deadline"]),
        ("user stories", ["user story", "as a user", "I want to"]),
        ("competitors", ["competitor", "competitive", "alternative"])
    ]

    for check_name, keywords in coverage_checks:
        if any(keyword.lower() in context_text.lower() for keyword in keywords):
            score += 10

    # Document diversity (max 20 points)
    file_count = get_file_count(project_id)
    if file_count >= 5:
        score += 20
    elif file_count >= 3:
        score += 15
    elif file_count >= 2:
        score += 10

    return min(score, 100)
```

#### Frontend Components

**1. Context Analysis Dashboard** (`components/ContextAnalysis.vue`)
```vue
<template>
  <div class="context-analysis">
    <!-- Quality Score Card -->
    <div class="quality-card">
      <div class="score-circle" :class="scoreClass">
        <span class="score-number">{{ analysis.quality_score }}</span>
        <span class="score-label">Quality Score</span>
      </div>
      <div class="score-description">
        <p v-if="analysis.quality_score >= 80">
          ✅ Excellent context! You're ready to generate a comprehensive PRD.
        </p>
        <p v-else-if="analysis.quality_score >= 60">
          ⚠️ Good context, but some areas could be improved.
        </p>
        <p v-else>
          ❌ Limited context. Consider adding more documents.
        </p>
      </div>
    </div>

    <!-- Coverage Checklist -->
    <div class="coverage-section">
      <h4>Coverage Checklist</h4>
      <div class="coverage-items">
        <div v-for="(value, key) in analysis.coverage" :key="key" class="coverage-item">
          <span class="coverage-icon">{{ value ? '✅' : '⚠️' }}</span>
          <span class="coverage-label">{{ formatLabel(key) }}</span>
        </div>
      </div>
    </div>

    <!-- Issues & Warnings -->
    <div v-if="analysis.issues.length > 0" class="issues-section">
      <h4>Issues Detected</h4>
      <div v-for="issue in analysis.issues" :key="issue.message"
           class="issue-item" :class="issue.severity">
        <span class="issue-icon">{{ getIssueIcon(issue.severity) }}</span>
        <div class="issue-content">
          <p class="issue-message">{{ issue.message }}</p>
          <p v-if="issue.sources" class="issue-sources">
            Sources: {{ issue.sources.join(', ') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Suggestions -->
    <div v-if="analysis.suggestions.length > 0" class="suggestions-section">
      <h4>💡 Suggestions to Improve</h4>
      <ul>
        <li v-for="suggestion in analysis.suggestions" :key="suggestion">
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>
```

**2. Document Summary Cards**
- Show summary for each uploaded document
- Key points extracted
- Entities mentioned (people, dates, metrics)
- Similarity to other docs

**3. Conflict Resolution Modal**
- Show conflicting statements side-by-side
- Let user choose which to keep
- Or manually resolve

#### Implementation Steps
1. ✅ **Week 1:** Context analysis API with AI summary
2. ✅ **Week 1:** Quality scoring algorithm
3. ✅ **Week 2:** Coverage detection logic
4. ✅ **Week 2:** Conflict/duplicate detection
5. ✅ **Week 3:** Context analysis dashboard UI
6. ✅ **Week 3:** Document summary cards
7. ✅ **Week 4:** Conflict resolution UI
8. ✅ **Week 4:** Testing, refinement

---

## Feature 6: Adaptive Questioning System

### Problem Statement
139 questions is overwhelming. Many questions are irrelevant based on context. The system should intelligently skip irrelevant questions and focus on what matters.

### User Stories
1. "I'm building a simple feature, not a full product. I shouldn't answer all 139 questions."
2. "The AI answered 50 questions with low confidence. I want to focus on reviewing only those."
3. "Based on my context, questions about 'mobile app' are irrelevant. Skip them automatically."
4. "If I answer 'No' to 'Is this a mobile app?', don't ask me iOS vs Android questions."

### Technical Design

#### Question Relevance Detection

**Method 1: Context-Based Filtering**
- Use AI to analyze context and determine relevant question categories
- Example: If context mentions "web app" but not "mobile", skip mobile-specific questions

**Method 2: Confidence Scoring**
- When AI prefills, assign confidence score (0.0 to 1.0) to each answer
- High confidence (>0.8): Auto-confirm
- Medium confidence (0.5-0.8): Show for review
- Low confidence (<0.5): Mark as "needs attention"

**Method 3: Dependency Logic**
- Questions have conditional dependencies
- If Q1 = "No", skip Q2-Q5
- Example: "Is this a mobile app?" → No → Skip all mobile questions

#### Database Changes

```sql
-- Add confidence scores to responses
ALTER TABLE question_responses ADD COLUMN confidence_score DECIMAL(3,2);
ALTER TABLE question_responses ADD COLUMN is_skipped BOOLEAN DEFAULT false;
ALTER TABLE question_responses ADD COLUMN skip_reason VARCHAR(255);

-- Track question relevance
CREATE TABLE question_relevance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    question_id VARCHAR(50),
    is_relevant BOOLEAN DEFAULT true,
    relevance_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_question_relevance_project ON question_relevance(project_id);
```

#### Enhanced questions.json Structure

```json
{
  "sections": [
    {
      "id": "1",
      "name": "Product Overview",
      "subsections": [
        {
          "id": "1.1",
          "name": "Basic Information",
          "questions": [
            {
              "id": "1.1.1",
              "question": "Is this a mobile application?",
              "type": "boolean",
              "hint": "Select Yes if building for iOS/Android",
              "skip_on_no": ["1.1.2", "1.1.3"], // Skip these if answer is No
              "relevance_keywords": ["mobile", "iOS", "Android", "app store"]
            },
            {
              "id": "1.1.2",
              "question": "Which platforms? (iOS, Android, both)",
              "type": "text",
              "depends_on": { "1.1.1": "Yes" }, // Only show if 1.1.1 = Yes
              "relevance_keywords": ["iOS", "Android", "mobile"]
            }
          ]
        }
      ]
    }
  ]
}
```

#### API Endpoints

**1. Analyze Question Relevance**
```
POST /api/questions/analyze-relevance/{project_id}
Response: {
  "total_questions": 139,
  "relevant_questions": 87,
  "skipped_questions": 52,
  "relevance_breakdown": {
    "mobile_questions": { "relevant": false, "count": 25 },
    "api_questions": { "relevant": true, "count": 30 },
    "compliance_questions": { "relevant": false, "count": 15 }
  }
}
```

**2. Smart Prefill with Confidence**
```
POST /api/questions/smart-prefill/{project_id}
Response: {
  "high_confidence_count": 45, // Auto-confirmed
  "medium_confidence_count": 30, // Needs review
  "low_confidence_count": 12, // Needs attention
  "skipped_count": 52 // Irrelevant
}
```

**3. Batch Confirm High Confidence**
```
POST /api/questions/batch-confirm/{project_id}
Body: { "min_confidence": 0.8 }
Response: { "confirmed_count": 45 }
```

**4. Get Filtered Questions**
```
GET /api/questions/filtered/{project_id}
Query: ?filter=needs_attention
Response: {
  "questions": [ /* Only low-confidence or unanswered */ ]
}
```

#### Frontend Components

**1. Smart Questions Dashboard** (`components/SmartQuestions.vue`)
```vue
<template>
  <div class="smart-questions">
    <!-- Filter Tabs -->
    <div class="question-filters">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">
        All ({{ stats.total }})
      </button>
      <button :class="{ active: filter === 'needs_attention' }" @click="filter = 'needs_attention'">
        ⚠️ Needs Attention ({{ stats.low_confidence }})
      </button>
      <button :class="{ active: filter === 'review' }" @click="filter = 'review'">
        👀 Review ({{ stats.medium_confidence }})
      </button>
      <button :class="{ active: filter === 'confirmed' }" @click="filter = 'confirmed'">
        ✅ Confirmed ({{ stats.confirmed }})
      </button>
      <button :class="{ active: filter === 'skipped' }" @click="filter = 'skipped'">
        ⏭ Skipped ({{ stats.skipped }})
      </button>
    </div>

    <!-- Bulk Actions -->
    <div class="bulk-actions">
      <button @click="confirmHighConfidence" class="btn btn-primary">
        ✅ Auto-Confirm High Confidence ({{ stats.high_confidence }})
      </button>
      <button @click="skipIrrelevant" class="btn btn-secondary">
        ⏭ Skip Irrelevant Questions
      </button>
    </div>

    <!-- Question List with Confidence Indicators -->
    <div class="question-list">
      <div v-for="question in filteredQuestions" :key="question.id"
           class="question-item" :class="getConfidenceClass(question.confidence)">
        <div class="question-header">
          <span class="question-id">{{ question.id }}</span>
          <span class="confidence-badge">
            {{ getConfidenceLabel(question.confidence) }}
          </span>
        </div>
        <div class="question-content">
          <p class="question-text">{{ question.question }}</p>
          <textarea v-model="question.response" />
        </div>
        <div class="question-actions">
          <button @click="confirmQuestion(question.id)">✅ Confirm</button>
          <button @click="skipQuestion(question.id)">⏭ Skip</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**2. Confidence Indicator**
- Green: High confidence (>0.8)
- Yellow: Medium confidence (0.5-0.8)
- Red: Low confidence (<0.5)
- Gray: Skipped (irrelevant)

**3. Relevance Explanation Tooltip**
- Show why a question was skipped
- "Skipped because context doesn't mention mobile apps"

**4. Question Dependencies Visualization**
- Show which questions depend on others
- Gray out dependent questions until parent is answered

#### Implementation Steps
1. ✅ **Week 1:** Enhance questions.json with dependencies and keywords
2. ✅ **Week 1:** Relevance analysis API with AI
3. ✅ **Week 2:** Confidence scoring in AI prefill
4. ✅ **Week 2:** Smart questions dashboard UI
5. ✅ **Week 3:** Bulk confirm/skip actions
6. ✅ **Week 3:** Question filtering and sorting
7. ✅ **Week 4:** Dependency logic and conditional display
8. ✅ **Week 4:** Testing, refinement

---

## Feature 8: Stakeholder View

### Problem Statement
Executives and stakeholders don't need 15 pages of technical details. They need a concise, visual summary for quick decision-making.

### User Stories
1. "I need to present this PRD to the CEO in 10 minutes. Give me a one-pager."
2. "I want to share just the executive summary and timeline, not the full technical spec."
3. "I want a clean presentation mode for screen sharing in meetings."
4. "I want to export a PDF summary for board meetings."

### Technical Design

#### Executive Summary Generation

**API Endpoint**
```
POST /api/prd/executive-summary/{project_id}
Response: {
  "summary": {
    "title": "User Analytics Dashboard",
    "tagline": "Empower PMs with real-time product insights",
    "problem": "PMs lack visibility into user behavior...",
    "solution": "An analytics dashboard that...",
    "success_metrics": ["50k MAU in Q1", "20% feature adoption"],
    "timeline": "Q2 2026 launch",
    "key_stakeholders": ["VP Product", "Engineering Lead"],
    "budget_estimate": "$150k",
    "risk_level": "Medium"
  },
  "one_pager_md": "# User Analytics Dashboard\n\n## Problem\n...",
  "slides": [ /* JSON for presentation slides */ ]
}
```

#### Frontend Components

**1. Stakeholder View** (`views/StakeholderView.vue`)
```vue
<template>
  <div class="stakeholder-view">
    <!-- One-Pager Summary -->
    <div class="one-pager">
      <h1>{{ summary.title }}</h1>
      <p class="tagline">{{ summary.tagline }}</p>

      <div class="summary-grid">
        <!-- Problem -->
        <div class="summary-card">
          <h3>🎯 Problem</h3>
          <p>{{ summary.problem }}</p>
        </div>

        <!-- Solution -->
        <div class="summary-card">
          <h3>💡 Solution</h3>
          <p>{{ summary.solution }}</p>
        </div>

        <!-- Success Metrics -->
        <div class="summary-card">
          <h3>📊 Success Metrics</h3>
          <ul>
            <li v-for="metric in summary.success_metrics" :key="metric">
              {{ metric }}
            </li>
          </ul>
        </div>

        <!-- Timeline -->
        <div class="summary-card">
          <h3>📅 Timeline</h3>
          <div class="timeline-viz">
            <!-- Visual timeline -->
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="stakeholder-actions">
        <button @click="exportPDF" class="btn btn-primary">
          📄 Export PDF
        </button>
        <button @click="togglePresentationMode" class="btn btn-secondary">
          🖥 Presentation Mode
        </button>
        <button @click="shareLink" class="btn btn-secondary">
          🔗 Share Link
        </button>
      </div>
    </div>
  </div>
</template>
```

**2. Presentation Mode**
- Full-screen, distraction-free
- Navigate with arrow keys
- One section per slide
- Clean, professional design

**3. PDF Export Styling**
- Professional formatting
- Company logo (optional)
- Page numbers
- Table of contents

#### Implementation Steps
1. ✅ **Week 1:** Executive summary extraction from PRD
2. ✅ **Week 1:** One-pager template design
3. ✅ **Week 2:** Stakeholder view UI
4. ✅ **Week 2:** Timeline visualization
5. ✅ **Week 3:** Presentation mode
6. ✅ **Week 3:** PDF export with styling
7. ✅ **Week 4:** Testing, polish

---

## Feature 9: AI Improvement Loop

### Problem Statement
AI doesn't always get it right. Let PMs teach the AI what "good" looks like by providing feedback on suggestions.

### User Stories
1. "The AI always writes too formally. I want it to learn my casual style."
2. "I always change 'users' to 'customers'. Train the AI to use my terminology."
3. "Rate this AI suggestion: thumbs up/down, so it learns for next time."
4. "Show me which sections I edit most, so I can improve my context documents."

### Technical Design

#### Database Changes

```sql
-- Feedback on AI suggestions
CREATE TABLE ai_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    question_id VARCHAR(50),
    ai_suggestion TEXT,
    user_correction TEXT,
    feedback_type VARCHAR(50), -- thumbs_up, thumbs_down, edited
    feedback_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_feedback_project ON ai_feedback(project_id);

-- Track editing patterns
CREATE TABLE edit_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100), -- word_replacement, tone_adjustment, etc.
    from_text TEXT,
    to_text TEXT,
    frequency INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### API Endpoints

**1. Submit AI Feedback**
```
POST /api/ai/feedback/{project_id}
Body: {
  "question_id": "1.1.1",
  "ai_suggestion": "Users will...",
  "user_correction": "Customers will...",
  "feedback_type": "edited",
  "reason": "We use 'customers' not 'users'"
}
```

**2. Get AI Insights**
```
GET /api/ai/insights/{project_id}
Response: {
  "total_suggestions": 139,
  "accepted": 95,
  "edited": 35,
  "rejected": 9,
  "common_edits": [
    { "from": "users", "to": "customers", "count": 12 },
    { "from": "utilize", "to": "use", "count": 8 }
  ],
  "most_edited_sections": [
    { "section": "Technical Requirements", "edit_count": 18 },
    { "section": "Success Metrics", "edit_count": 12 }
  ]
}
```

**3. Apply Learned Preferences** (Future enhancement)
```
POST /api/ai/apply-preferences/{project_id}
Body: { "preferences": [ ... ] }
Response: { "updated_responses": 23 }
```

#### Frontend Components

**1. AI Feedback Widget** (inline with questions)
```vue
<template>
  <div class="ai-response">
    <div class="ai-suggestion">
      <span class="ai-badge">✨ AI Suggestion</span>
      <p>{{ aiSuggestion }}</p>
    </div>

    <!-- Feedback Buttons -->
    <div class="feedback-actions">
      <button @click="thumbsUp" :class="{ active: feedback === 'up' }">
        👍 Good
      </button>
      <button @click="thumbsDown" :class="{ active: feedback === 'down' }">
        👎 Not Helpful
      </button>
      <button @click="showEditReason">
        ✏️ Edited
      </button>
    </div>

    <!-- Edit Reason Modal -->
    <div v-if="showReasonModal" class="reason-modal">
      <textarea v-model="editReason" placeholder="Why did you edit this? (Optional)" />
      <button @click="submitFeedback">Submit</button>
    </div>
  </div>
</template>
```

**2. AI Insights Dashboard** (`components/AIInsights.vue`)
- Show acceptance rate
- Common edits and replacements
- Most edited sections
- Suggestions for improving context

**3. Preferences Manager**
- User can define preferences:
  - Tone: Formal / Casual / Technical
  - Terminology: users → customers
  - Length: Concise / Detailed
- AI applies preferences in future generations

#### Implementation Steps
1. ✅ **Week 1:** Database schema for feedback
2. ✅ **Week 1:** Feedback submission API
3. ✅ **Week 2:** Inline feedback widgets
4. ✅ **Week 2:** Track edit patterns
5. ✅ **Week 3:** AI insights dashboard
6. ✅ **Week 3:** Preferences manager
7. ✅ **Week 4:** Apply learned preferences (basic)
8. ✅ **Week 4:** Testing, refinement

---

## Feature 10: Analytics & Insights

### Problem Statement
PMs can't see patterns in their PRD creation process. Which sections always need heavy editing? How long does it take on average? What can be improved?

### User Stories
1. "I want to see how long it takes me to complete a PRD on average."
2. "I want to know which sections I always edit heavily, so I can improve my context docs."
3. "I want to see my PRD completion rate over time (trend)."
4. "I want to benchmark against team averages (if multi-user)."

### Technical Design

#### Database Changes

```sql
-- Track PRD metrics
CREATE TABLE prd_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    metric_type VARCHAR(100), -- time_to_complete, edit_count, context_size, etc.
    metric_value DECIMAL(10,2),
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prd_metrics_project ON prd_metrics(project_id);
CREATE INDEX idx_prd_metrics_type ON prd_metrics(metric_type);

-- Track time spent
CREATE TABLE time_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    tab_name VARCHAR(50), -- context, features, questions, prd
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### API Endpoints

**1. Get Project Analytics**
```
GET /api/analytics/project/{project_id}
Response: {
  "time_metrics": {
    "total_time_minutes": 145,
    "time_by_tab": {
      "context": 25,
      "features": 30,
      "questions": 60,
      "prd": 30
    },
    "time_to_first_prd": 120 // minutes from project creation to first PRD
  },
  "quality_metrics": {
    "context_quality_score": 85,
    "questions_confirmed_percentage": 75,
    "edit_count": 23
  },
  "completion_metrics": {
    "started_at": "2026-01-20T10:00:00Z",
    "first_prd_at": "2026-01-20T12:00:00Z",
    "status": "completed"
  }
}
```

**2. Get User Analytics** (across all projects)
```
GET /api/analytics/user
Response: {
  "total_projects": 12,
  "completed_projects": 8,
  "avg_time_to_complete_minutes": 135,
  "avg_questions_confirmed": 95,
  "most_used_sections": ["Goals", "Features", "Success Metrics"],
  "trends": {
    "prds_per_month": [3, 5, 4, 6],
    "avg_quality_score": [65, 72, 78, 85]
  }
}
```

**3. Get Team Analytics** (future: multi-user)
```
GET /api/analytics/team
Response: {
  "team_avg_completion_time": 150,
  "fastest_pm": { "name": "Alice", "avg_time": 90 },
  "most_thorough_pm": { "name": "Bob", "avg_questions": 120 }
}
```

#### Frontend Components

**1. Analytics Dashboard** (`views/AnalyticsDashboard.vue`)
```vue
<template>
  <div class="analytics-dashboard">
    <h2>Your PRD Analytics</h2>

    <!-- Time Metrics -->
    <div class="metrics-section">
      <h3>⏱ Time Metrics</h3>
      <div class="metric-cards">
        <div class="metric-card">
          <span class="metric-value">{{ avgTimeToComplete }}</span>
          <span class="metric-label">Avg Time to Complete</span>
        </div>
        <div class="metric-card">
          <span class="metric-value">{{ totalProjects }}</span>
          <span class="metric-label">Total Projects</span>
        </div>
        <div class="metric-card">
          <span class="metric-value">{{ completionRate }}%</span>
          <span class="metric-label">Completion Rate</span>
        </div>
      </div>
    </div>

    <!-- Quality Trends -->
    <div class="metrics-section">
      <h3>📈 Quality Trends</h3>
      <canvas ref="qualityChart"></canvas>
    </div>

    <!-- Most Edited Sections -->
    <div class="metrics-section">
      <h3>✏️ Most Edited Sections</h3>
      <div class="section-edits">
        <div v-for="section in mostEditedSections" :key="section.name"
             class="section-edit-bar">
          <span class="section-name">{{ section.name }}</span>
          <div class="bar" :style="{ width: section.percentage + '%' }"></div>
          <span class="edit-count">{{ section.count }} edits</span>
        </div>
      </div>
    </div>

    <!-- Insights & Recommendations -->
    <div class="insights-section">
      <h3>💡 Insights</h3>
      <ul>
        <li>You spend most time on the Questions tab (60 min avg). Consider using AI prefill more.</li>
        <li>Your context quality score improved from 65 to 85 over the last 4 PRDs. Keep it up!</li>
        <li>Technical Requirements section gets edited the most (18 times). Add more technical context docs.</li>
      </ul>
    </div>
  </div>
</template>
```

**2. Project Analytics Tab** (within each project)
- Show metrics for current project
- Time breakdown by tab
- Edit heatmap
- Context quality over time

**3. Charts & Visualizations**
- Use Chart.js or similar
- Line chart: Quality score over time
- Bar chart: Time spent per tab
- Pie chart: Sections distribution

#### Implementation Steps
1. ✅ **Week 1:** Database schema for metrics
2. ✅ **Week 1:** Time tracking implementation
3. ✅ **Week 2:** Analytics API endpoints
4. ✅ **Week 2:** Analytics dashboard UI
5. ✅ **Week 3:** Charts and visualizations
6. ✅ **Week 3:** Insights generation
7. ✅ **Week 4:** Testing, polish

---

## Implementation Timeline (Overall)

### Phase 1: Foundation (Weeks 1-8)
- **Weeks 1-4:** Feature 1 (PRD Editing)
- **Weeks 5-8:** Feature 2 (Templates)

### Phase 2: Collaboration (Weeks 9-16)
- **Weeks 9-13:** Feature 3 (Collaboration & Sharing)
- **Weeks 14-16:** Feature 4 (Version History)

### Phase 3: Intelligence (Weeks 17-24)
- **Weeks 17-20:** Feature 5 (Smart Context Analysis)
- **Weeks 21-24:** Feature 6 (Adaptive Questions)

### Phase 4: Polish (Weeks 25-32)
- **Weeks 25-28:** Feature 8 (Stakeholder View)
- **Weeks 29-30:** Feature 9 (AI Improvement)
- **Weeks 31-32:** Feature 10 (Analytics)

**Total: 32 weeks (8 months)**

---

## Technical Dependencies

### Backend Stack
- Python 3.12
- Anthropic Claude API (Sonnet 4.5)
- Supabase PostgreSQL
- Vercel Serverless Functions

### Frontend Stack
- Vue 3 + Vite
- Pinia (state management)
- Chart.js (analytics visualizations)
- Marked (markdown rendering)
- diff-match-patch (version comparison)

### New Libraries Needed
- **PDF Export:** `pdfkit` or `weasyprint`
- **Diff Viewer:** `diff-match-patch`
- **Rich Text Editor:** Consider CodeMirror or Monaco for markdown editing
- **Charts:** Chart.js or D3.js

---

## Database Migration Strategy

All schema changes will be applied incrementally:
1. Create migration SQL files
2. Test on staging database
3. Run migrations on production with backups
4. Add rollback scripts for each migration

---

## Testing Strategy

For each feature:
1. Unit tests for API endpoints
2. Integration tests for database queries
3. Frontend component tests (Vue Test Utils)
4. End-to-end tests (Playwright or Cypress)
5. Add to EVALS.md and run_evals.sh

---

## Success Metrics

### Feature 1 (Editing)
- 80% of users edit their PRD at least once
- Avg 5-10 edits per PRD

### Feature 2 (Templates)
- 60% of users choose non-default template
- 20% of users create custom template

### Feature 3 (Collaboration)
- 40% of PRDs are shared
- Avg 3 comments per shared PRD

### Feature 4 (Versions)
- Avg 3 versions per PRD
- 30% of users restore a previous version

### Feature 5 (Context Analysis)
- Context quality score improves by 15% on avg
- 50% reduction in "missing info" warnings

### Feature 6 (Adaptive Questions)
- 30-40% reduction in questions answered
- 20% faster PRD completion time

### Feature 8 (Stakeholder View)
- 50% of users export executive summary
- Avg 2 stakeholder views per PRD

### Feature 9 (AI Improvement)
- 70% thumbs-up rate on AI suggestions
- 10% improvement in AI accuracy over time

### Feature 10 (Analytics)
- 80% of users view analytics at least once
- Insights lead to 15% faster PRD creation

---

## Next Steps

1. Review this roadmap
2. Prioritize features (which to build first?)
3. Create detailed tickets for Phase 1
4. Set up project tracking (Linear/Jira)
5. Begin implementation

Would you like me to create implementation plans for specific features, or shall we proceed with development?
