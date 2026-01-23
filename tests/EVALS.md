# PM Clarity - Comprehensive Evaluation Suite

**Version**: 3.0
**Date**: 2026-01-23
**Coverage**: Core Features + 9 Advanced Features

---

## Quick Reference

| Category | Total Tests | Critical |
|----------|-------------|----------|
| API Health | 2 | 2 |
| Projects | 5 | 5 |
| Context Files | 6 | 5 |
| Features | 7 | 6 |
| Questions | 8 | 7 |
| PRD Generation | 5 | 5 |
| PRD Editing & Refinement | 5 | 4 |
| Templates & Customization | 5 | 3 |
| Collaboration & Sharing | 8 | 5 |
| Version History & Comparison | 3 | 2 |
| Smart Context Analysis | 6 | 4 |
| Adaptive Questioning | 6 | 4 |
| Stakeholder Views | 5 | 3 |
| AI Improvement Loop | 6 | 4 |
| Analytics & Insights | 6 | 3 |
| Frontend UI | 8 | 6 |
| Data Consistency | 8 | 6 |
| User Guidance | 6 | 4 |
| Edge Cases | 5 | 3 |
| Integration Tests | 5 | 2 |
| **Total** | **115** | **83** |

---

## Table of Contents

### Core Features
1. [API Health Checks](#1-api-health-checks)
2. [Projects API](#2-projects-api)
3. [Context Files API](#3-context-files-api)
4. [Features API](#4-features-api)
5. [Questions API](#5-questions-api)
6. [PRD Generation API](#6-prd-generation-api)

### Advanced Features
7. [PRD Editing & Refinement](#7-prd-editing--refinement)
8. [Templates & Customization](#8-templates--customization)
9. [Collaboration & Sharing](#9-collaboration--sharing)
10. [Version History & Comparison](#10-version-history--comparison)
11. [Smart Context Analysis](#11-smart-context-analysis)
12. [Adaptive Questioning](#12-adaptive-questioning)
13. [Stakeholder Views](#13-stakeholder-views)
14. [AI Improvement Loop](#14-ai-improvement-loop)
15. [Analytics & Insights](#15-analytics--insights)

### Integration & Quality
16. [Frontend UI Tests](#16-frontend-ui-tests)
17. [Data Consistency Tests](#17-data-consistency-tests)
18. [User Guidance Tests](#18-user-guidance-tests)
19. [Edge Cases & Error Handling](#19-edge-cases--error-handling)
20. [Integration Tests](#20-integration-tests)

---

## Test Environment Setup

```bash
# Set base URL
export API_URL="https://pm-clarity.vercel.app"

# Or for local testing
export API_URL="http://localhost:5001"

# Create test project and get ID
PROJECT_ID=$(curl -X POST "$API_URL/api/projects" \
  -H "Content-Type: application/json" \
  -d '{"name":"Comprehensive Test Project"}' \
  | jq -r '.id')

echo "Test Project ID: $PROJECT_ID"
```

---

## 1. API Health Checks

### EVAL-001: Health Endpoint
**Priority:** Critical
**Endpoint:** `GET /api/health`
**Expected:** 200 OK with `{"status": "ok"}`

```bash
curl -s https://pm-clarity.vercel.app/api/health
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains `"status": "ok"`

---

### EVAL-002: CORS Headers
**Priority:** Critical
**Endpoint:** `OPTIONS /api/projects`
**Expected:** CORS headers present

```bash
curl -s -X OPTIONS https://pm-clarity.vercel.app/api/projects -i | head -20
```

**Pass Criteria:**
- [ ] `Access-Control-Allow-Origin: *` present
- [ ] `Access-Control-Allow-Methods` includes GET, POST, DELETE

---

## 2. Projects API

### EVAL-003: List Projects
**Priority:** Critical
**Endpoint:** `GET /api/projects`

```bash
curl -s https://pm-clarity.vercel.app/api/projects
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response is a JSON array
- [ ] Each project has: id, name, created_at

---

### EVAL-004: Create Project
**Priority:** Critical
**Endpoint:** `POST /api/projects`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Eval Test Project"}'
```

**Pass Criteria:**
- [ ] Returns HTTP 201
- [ ] Response contains new project with valid UUID
- [ ] Project name matches input

---

### EVAL-005: Create Project - Validation
**Priority:** High
**Expected:** 400 Bad Request for empty name

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": ""}'
```

**Pass Criteria:**
- [ ] Returns HTTP 400
- [ ] Error message indicates name is required

---

### EVAL-006: Get Single Project
**Priority:** High
**Endpoint:** `GET /api/projects/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/projects/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains project details

---

### EVAL-007: Delete Project
**Priority:** Critical
**Endpoint:** `DELETE /api/projects/{project_id}`

```bash
curl -s -X DELETE https://pm-clarity.vercel.app/api/projects/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Project no longer appears in list

---

## 3. Context Files API

### EVAL-008: List Context Files
**Priority:** Critical
**Endpoint:** `GET /api/context/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/context/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response is a JSON array
- [ ] Each file has: id, file_name, file_type, extracted_text

---

### EVAL-009: Upload Context File (TXT)
**Priority:** Critical
**Endpoint:** `POST /api/context/upload/{project_id}`

```bash
echo "Test content for evaluation" > /tmp/test_eval.txt
curl -s -X POST https://pm-clarity.vercel.app/api/context/upload/{PROJECT_ID} \
  -F "files=@/tmp/test_eval.txt"
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response shows successful upload
- [ ] File appears in context list

---

### EVAL-010: Upload Context File (PDF)
**Priority:** High
**Expected:** 200 OK with extracted text

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Text is extracted from PDF
- [ ] extracted_text field is populated

---

### EVAL-011: Get Aggregated Context Text
**Priority:** Critical
**Endpoint:** `GET /api/context/text/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/context/text/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains `text`, `length`, `has_content`
- [ ] Text combines all context files

---

### EVAL-012: Delete Context File
**Priority:** High
**Endpoint:** `DELETE /api/context/file/{file_id}`

```bash
curl -s -X DELETE https://pm-clarity.vercel.app/api/context/file/{FILE_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] File no longer appears in list

---

### EVAL-013: Upload Invalid File Type
**Priority:** Medium
**Expected:** Error for unsupported file type

**Pass Criteria:**
- [ ] Returns error for .exe, .zip, etc.
- [ ] Error message indicates unsupported type

---

## 4. Features API

### EVAL-014: List Features
**Priority:** Critical
**Endpoint:** `GET /api/features/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/features/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response is a JSON array
- [ ] Each feature has: id, name, description, is_selected

---

### EVAL-015: Extract Features with AI
**Priority:** Critical
**Endpoint:** `POST /api/features/extract/{project_id}`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/features/extract/{PROJECT_ID} \
  -H "Content-Type: application/json"
```

**Pass Criteria:**
- [ ] Returns HTTP 200 (within 60 seconds)
- [ ] Response contains extracted features array
- [ ] Features have name and description
- [ ] Features are saved to database

---

### EVAL-016: Extract Features - No Context
**Priority:** High
**Expected:** 400 error when no context uploaded

**Pass Criteria:**
- [ ] Returns HTTP 400
- [ ] Error indicates context is required

---

### EVAL-017: Create Manual Feature
**Priority:** High
**Endpoint:** `POST /api/features/{project_id}`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/features/{PROJECT_ID} \
  -H "Content-Type: application/json" \
  -d '{"name": "Manual Feature", "description": "Test description"}'
```

**Pass Criteria:**
- [ ] Returns HTTP 201
- [ ] Feature is created with provided data
- [ ] `is_ai_generated` is false

---

### EVAL-018: Toggle Feature Selection
**Priority:** High
**Endpoint:** `PUT /api/features/select/{feature_id}`

```bash
curl -s -X PUT https://pm-clarity.vercel.app/api/features/select/{FEATURE_ID} \
  -H "Content-Type: application/json" \
  -d '{"is_selected": false}'
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] `is_selected` value is updated

---

### EVAL-019: Update Feature
**Priority:** Medium
**Endpoint:** `PUT /api/features/item/{feature_id}`

```bash
curl -s -X PUT https://pm-clarity.vercel.app/api/features/item/{FEATURE_ID} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Feature name is updated

---

### EVAL-020: Delete Feature
**Priority:** High
**Endpoint:** `DELETE /api/features/item/{feature_id}`

```bash
curl -s -X DELETE https://pm-clarity.vercel.app/api/features/item/{FEATURE_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Feature no longer appears in list

---

## 5. Questions API

### EVAL-021: Get Questions Structure
**Priority:** Critical
**Endpoint:** `GET /api/questions`

```bash
curl -s https://pm-clarity.vercel.app/api/questions
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains `sections` array
- [ ] Each section has subsections with questions
- [ ] Questions have: id, question, type, hint

---

### EVAL-022: Get Question Responses
**Priority:** Critical
**Endpoint:** `GET /api/questions/responses/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/questions/responses/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response is a JSON array
- [ ] Each response has: question_id, response, confirmed

---

### EVAL-023: AI Prefill Questions
**Priority:** Critical
**Endpoint:** `POST /api/questions/prefill/{project_id}`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/questions/prefill/{PROJECT_ID} \
  -H "Content-Type: application/json"
```

**Pass Criteria:**
- [ ] Returns HTTP 200 (within 5 minutes)
- [ ] Response contains prefilled answers
- [ ] Answers are saved with `ai_suggested: true`
- [ ] Multiple questions are answered

---

### EVAL-024: AI Prefill - No Context
**Priority:** High
**Expected:** 400 error when no context

**Pass Criteria:**
- [ ] Returns HTTP 400
- [ ] Error indicates context is required

---

### EVAL-025: Save Single Response
**Priority:** High
**Endpoint:** `PUT /api/questions/response/{project_id}/{question_id}`

```bash
curl -s -X PUT https://pm-clarity.vercel.app/api/questions/response/{PROJECT_ID}/1.1.1 \
  -H "Content-Type: application/json" \
  -d '{"response": "Test answer", "confirmed": false}'
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response is saved to database

---

### EVAL-026: Confirm Response
**Priority:** High
**Endpoint:** `POST /api/questions/confirm/{project_id}/{question_id}`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/questions/confirm/{PROJECT_ID}/1.1.1 \
  -H "Content-Type: application/json" \
  -d '{"confirmed": true}'
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] `confirmed` is set to true

---

### EVAL-027: Get Question Stats
**Priority:** High
**Endpoint:** `GET /api/questions/stats/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/questions/stats/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains: total_questions, answered, confirmed
- [ ] `completion_percentage` is calculated correctly

---

### EVAL-028: Bulk Save Responses
**Priority:** Medium
**Endpoint:** `PUT /api/questions/responses/{project_id}`

```bash
curl -s -X PUT https://pm-clarity.vercel.app/api/questions/responses/{PROJECT_ID} \
  -H "Content-Type: application/json" \
  -d '{"responses": [{"question_id": "1.1.1", "response": "Answer 1"}, {"question_id": "1.1.2", "response": "Answer 2"}]}'
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] All responses are saved

---

## 6. PRD Generation API

### EVAL-029: Generate PRD
**Priority:** Critical
**Endpoint:** `POST /api/prd/generate/{project_id}`

```bash
curl -s -X POST https://pm-clarity.vercel.app/api/prd/generate/{PROJECT_ID} \
  -H "Content-Type: application/json"
```

**Pass Criteria:**
- [ ] Returns HTTP 200 (within 2 minutes)
- [ ] Response contains PRD in markdown format
- [ ] PRD is saved to database
- [ ] Contains standard PRD sections

---

### EVAL-030: Generate PRD - No Responses
**Priority:** High
**Expected:** 400 error when no confirmed responses

**Pass Criteria:**
- [ ] Returns HTTP 400
- [ ] Error indicates responses required

---

### EVAL-031: Get PRD
**Priority:** Critical
**Endpoint:** `GET /api/prd/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/prd/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains `content_md`
- [ ] Returns most recent PRD

---

### EVAL-032: Preview PRD (HTML)
**Priority:** High
**Endpoint:** `GET /api/prd/preview/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/prd/preview/{PROJECT_ID}
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Response contains `markdown` and `html`
- [ ] HTML is properly formatted

---

### EVAL-033: Export PRD as Markdown
**Priority:** High
**Endpoint:** `GET /api/prd/export/md/{project_id}`

```bash
curl -s https://pm-clarity.vercel.app/api/prd/export/md/{PROJECT_ID} -o prd.md
```

**Pass Criteria:**
- [ ] Returns HTTP 200
- [ ] Content-Type is text/markdown
- [ ] Content-Disposition header present
- [ ] File downloads correctly

---

## 7. PRD Editing & Refinement

### EVAL-034: Edit PRD Content
**Priority:** Critical
**Endpoint:** `PUT /api/prd/edit/{project_id}`

```bash
curl -X PUT "$API_URL/api/prd/edit/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "content_md": "# Updated PRD\n\n## Executive Summary\nThis is the updated version."
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Response contains updated content
- [ ] Version number incremented

**UI Test:**
1. Open PRD tab
2. Click "✏️ Edit PRD"
3. Modify content in editor
4. Click "Save"
5. Verify changes reflected in preview

---

### EVAL-035: Version History
**Priority:** High
**Endpoint:** `GET /api/prd/history/{project_id}`

```bash
curl "$API_URL/api/prd/history/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Returns array of snapshots
- [ ] Each snapshot has: id, version_name, created_at, change_summary
- [ ] Ordered by creation date (newest first)

---

### EVAL-036: Save Named Version
**Priority:** High
**Endpoint:** `POST /api/prd/save-version/{project_id}`

```bash
curl -X POST "$API_URL/api/prd/save-version/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "version_name": "v1.0 - Initial Release",
    "change_summary": "Added technical requirements section"
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Snapshot created with custom name
- [ ] Appears in version history

---

### EVAL-037: Restore Version
**Priority:** High
**Endpoint:** `POST /api/prd/restore/{project_id}/{snapshot_id}`

```bash
SNAPSHOT_ID="<snapshot-id-from-history>"
curl -X POST "$API_URL/api/prd/restore/$PROJECT_ID/$SNAPSHOT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Current PRD content matches snapshot content
- [ ] New snapshot created (before restore)

---

### EVAL-038: Regenerate Section
**Priority:** Medium
**Endpoint:** `POST /api/prd/regenerate-section/{project_id}`

```bash
curl -X POST "$API_URL/api/prd/regenerate-section/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"section_name": "Technical Requirements"}'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Section content regenerated
- [ ] Other sections unchanged
- [ ] AI uses latest context and responses

---

## 8. Templates & Customization

### EVAL-039: List Templates
**Priority:** Critical
**Endpoint:** `GET /api/templates`

```bash
curl "$API_URL/api/templates"
```

**Pass Criteria:**
- [ ] Returns array of templates
- [ ] Contains 5 default templates: Lean PRD, Detailed PRD, Technical Spec, One-Pager, Feature Brief
- [ ] Each has: id, name, description, sections

---

### EVAL-040: Get Template Details
**Priority:** High
**Endpoint:** `GET /api/templates/{template_id}`

```bash
TEMPLATE_ID="<template-id>"
curl "$API_URL/api/templates/$TEMPLATE_ID"
```

**Pass Criteria:**
- [ ] Returns template with full section details
- [ ] Sections include: title, description, questions
- [ ] Questions have: id, text, type, hint

---

### EVAL-041: Create Custom Template
**Priority:** Medium
**Endpoint:** `POST /api/templates`

```bash
curl -X POST "$API_URL/api/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Integration PRD",
    "description": "Template for API integration projects",
    "sections": [
      {
        "title": "API Overview",
        "description": "High-level API description",
        "display_order": 1
      }
    ]
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Template created with unique ID
- [ ] Appears in template list

---

### EVAL-042: Clone Template
**Priority:** Medium
**Endpoint:** `POST /api/templates/{template_id}/clone`

```bash
curl -X POST "$API_URL/api/templates/$TEMPLATE_ID/clone" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Custom Lean PRD"}'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] New template created with all sections copied
- [ ] New name applied
- [ ] Original template unchanged

---

### EVAL-043: Template Selection in Project Creation
**UI Test:**
1. Click "+ New Project"
2. Enter project name
3. Click "Next: Choose Template"
4. Verify 5+ templates displayed
5. Select template
6. Click "Create Project"
7. Verify project uses selected template

**Pass Criteria:**
- [ ] All templates visible with descriptions
- [ ] Preview shows template structure
- [ ] Project creation succeeds
- [ ] Questions reflect template sections

---

## 9. Collaboration & Sharing

### EVAL-044: Create Share Link
**Priority:** High
**Endpoint:** `POST /api/share/create/{project_id}`

```bash
curl -X POST "$API_URL/api/share/create/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "access_level": "view",
    "password": "test123",
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Returns share_token and share_url
- [ ] Access level set correctly

---

### EVAL-045: Access Shared PRD
**Priority:** High
**Endpoint:** `GET /api/share/{share_token}`

```bash
SHARE_TOKEN="<token-from-previous-test>"
curl "$API_URL/api/share/$SHARE_TOKEN?password=test123"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Returns PRD content
- [ ] Includes project metadata
- [ ] Access level enforced

---

### EVAL-046: Invalid Password
**Priority:** Medium
**Expected:** 403 error with wrong password

```bash
curl "$API_URL/api/share/$SHARE_TOKEN?password=wrong"
```

**Pass Criteria:**
- [ ] Status 403
- [ ] Error: "Invalid password"

---

### EVAL-047: List Share Links
**Priority:** Medium
**Endpoint:** `GET /api/share/list/{project_id}`

```bash
curl "$API_URL/api/share/list/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Returns array of share links
- [ ] Each includes: token, access_level, created_at, expires_at, access_count

---

### EVAL-048: Revoke Share
**Priority:** High
**Endpoint:** `DELETE /api/share/revoke/{share_id}`

```bash
SHARE_ID="<share-id>"
curl -X DELETE "$API_URL/api/share/revoke/$SHARE_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Share link no longer accessible
- [ ] Returns confirmation message

---

### EVAL-049: Add Comment
**Priority:** Medium
**Endpoint:** `POST /api/comments/{prd_id}/add`

```bash
PRD_ID="<prd-id>"
curl -X POST "$API_URL/api/comments/$PRD_ID/add" \
  -H "Content-Type: application/json" \
  -d '{
    "author_name": "Test User",
    "comment_text": "This section needs more detail",
    "section_reference": "Technical Requirements"
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Comment saved with timestamp
- [ ] Appears in comments list

---

### EVAL-050: Reply to Comment
**Priority:** Medium
**Endpoint:** `POST /api/comments/reply/{comment_id}`

```bash
COMMENT_ID="<parent-comment-id>"
curl -X POST "$API_URL/api/comments/reply/$COMMENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "author_name": "PM Owner",
    "comment_text": "Good point, I will expand this section"
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Reply linked to parent comment
- [ ] Thread structure maintained

---

### EVAL-051: Resolve Comment
**Priority:** Low
**Endpoint:** `POST /api/comments/resolve/{comment_id}`

```bash
curl -X POST "$API_URL/api/comments/resolve/$COMMENT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Comment marked resolved
- [ ] resolved_at timestamp set

---

## 10. Version History & Comparison

### EVAL-052: Compare Versions
**Priority:** High
**Endpoint:** `POST /api/prd/compare/{project_id}`

```bash
VERSION1_ID="<snapshot-id-1>"
VERSION2_ID="<snapshot-id-2>"

curl -X POST "$API_URL/api/prd/compare/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "version1_id": "'$VERSION1_ID'",
    "version2_id": "'$VERSION2_ID'"
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Returns diff object with: added_lines, removed_lines, total_changes
- [ ] Diff text in unified format

---

### EVAL-053: Generate Changelog
**Priority:** Medium
**Endpoint:** `POST /api/prd/changelog/{project_id}`

```bash
curl -X POST "$API_URL/api/prd/changelog/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "from_version_id": "'$VERSION1_ID'",
    "to_version_id": "'$VERSION2_ID'",
    "version_name": "v1.1 Release Notes"
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Returns formatted changelog
- [ ] Highlights key changes
- [ ] Organized by section

---

### EVAL-054: Get Specific Snapshot
**Priority:** Medium
**Endpoint:** `GET /api/prd/snapshot/{snapshot_id}`

```bash
curl "$API_URL/api/prd/snapshot/$SNAPSHOT_ID"
```

**Pass Criteria:**
- [ ] Returns complete snapshot
- [ ] Includes: content_md, version_name, created_at, change_summary

---

## 11. Smart Context Analysis

### EVAL-055: Basic Quality Analysis
**Priority:** Critical
**Endpoint:** `GET /api/context/analyze/{project_id}`

```bash
curl "$API_URL/api/context/analyze/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Returns quality_score (0-100)
- [ ] Coverage object with 8 categories
- [ ] Suggestions array
- [ ] Summary text
- [ ] Metrics breakdown

**Expected Coverage Categories:**
1. user_personas
2. success_metrics
3. technical_requirements
4. timeline
5. user_stories
6. competitors
7. constraints
8. scope

---

### EVAL-056: Entity Extraction
**Priority:** High
**Test:** Extract dates, percentages, monetary values

```bash
curl "$API_URL/api/context/analyze/$PROJECT_ID" | jq '.entities'
```

**Pass Criteria:**
- [ ] dates array with extracted dates
- [ ] percentages array (e.g., "25%", "50%")
- [ ] monetary array (e.g., "$100K", "$1M")
- [ ] technical_terms array (acronyms, tech keywords)

---

### EVAL-057: Conflict Detection
**Priority:** Medium
**Test:** Identify contradictions

```bash
curl "$API_URL/api/context/analyze/$PROJECT_ID" | jq '.conflicts'
```

**Pass Criteria:**
- [ ] conflicts array
- [ ] Each conflict has: type, terms, message
- [ ] Detects contradictory pairs (e.g., "required" vs "optional")

---

### EVAL-058: AI Deep Analysis
**Priority:** High
**Endpoint:** `POST /api/context/analyze/{project_id}`

```bash
curl -X POST "$API_URL/api/context/analyze/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] ai_analysis object included
- [ ] Contains: key_themes, stakeholders_mentioned, potential_risks, missing_info, recommendations
- [ ] All AI fields are arrays with relevant items

---

### EVAL-059: File Summarization
**Priority:** Medium
**Endpoint:** `GET /api/context/summarize/{file_id}`

```bash
FILE_ID="<context-file-id>"
curl "$API_URL/api/context/summarize/$FILE_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] summary text (2-3 sentences)
- [ ] key_points array (3-5 items)
- [ ] document_type classification
- [ ] relevance_score (1-10)

---

### EVAL-060: UI Quality Dashboard
**UI Test:**
1. Upload context files
2. Scroll to "Context Quality Analysis"
3. Verify quality score circle displays
4. Check coverage grid (8 categories)
5. Review suggestions list
6. Verify entities extracted
7. Check for conflict warnings
8. Click "🤖 Deep Analysis"
9. Verify AI insights appear

**Pass Criteria:**
- [ ] Quality score color-coded (red <40, yellow 40-79, green 80+)
- [ ] All 8 coverage categories shown
- [ ] Missing categories flagged with ❌
- [ ] Entities displayed in tags
- [ ] AI analysis shows themes, risks, recommendations

---

## 12. Adaptive Questioning

### EVAL-061: Get Follow-Up Questions
**Priority:** High
**Endpoint:** `POST /api/questions/follow-ups/{project_id}/{question_id}`

```bash
QUESTION_ID="1.1.1"

curl -X POST "$API_URL/api/questions/follow-ups/$PROJECT_ID/$QUESTION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "We are competing with Figma and Sketch in the design tool market",
    "question": "Who are your main competitors?",
    "include_ai": true
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] follow_ups array (rule-based triggers)
- [ ] ai_follow_ups array (if include_ai=true)
- [ ] related_questions array
- [ ] skip_questions array (if applicable)

---

### EVAL-062: Rule-Based Follow-Ups
**Priority:** High
**Test:** Verify keyword triggers work

**Test Cases:**
| Response Contains | Expected Follow-Up Category |
|-------------------|----------------------------|
| "competitor", "Figma" | competitor |
| "Q2 2026", "deadline" | timeline |
| "conversion rate", "KPI" | metric |
| "user", "customer segment" | user |
| "API integration", "third-party" | integration |

**Pass Criteria:**
- [ ] Each keyword triggers appropriate follow-ups
- [ ] Max 3 follow-ups per response
- [ ] No duplicate follow-ups

---

### EVAL-063: Skip Logic
**Priority:** Medium
**Test:** Questions skipped based on response

```bash
curl -X POST "$API_URL/api/questions/follow-ups/$PROJECT_ID/2.1.1" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "No competitors, this is a unique solution",
    "question": "Who are your competitors?"
  }'
```

**Pass Criteria:**
- [ ] skip_questions array includes ["2.1.2", "2.1.3"]
- [ ] Skipped questions not shown in UI

---

### EVAL-064: Save Follow-Up Response
**Priority:** Medium
**Endpoint:** `POST /api/questions/save-follow-up/{project_id}`

```bash
curl -X POST "$API_URL/api/questions/save-follow-up/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "follow_up_id": "fu_competitor_1",
    "parent_question_id": "2.1.1",
    "question": "How do you plan to differentiate?",
    "response": "We focus on real-time collaboration which competitors lack"
  }'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Follow-up saved as question response
- [ ] Linked to parent question via metadata

---

### EVAL-065: Smart Suggestion
**Priority:** High
**Endpoint:** `POST /api/questions/smart-suggest/{project_id}/{question_id}`

```bash
curl -X POST "$API_URL/api/questions/smart-suggest/$PROJECT_ID/$QUESTION_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your target launch date?"}'
```

**Pass Criteria:**
- [ ] Status 200
- [ ] suggested_answer based on context
- [ ] confidence level (high/medium/low)
- [ ] reasoning text explaining suggestion

---

### EVAL-066: UI Navigation
**UI Test:**
1. Confirm a question with substantial answer
2. Verify follow-up questions appear below
3. Answer a follow-up question
4. Click related question link
5. Verify scroll to and highlight target question

**Pass Criteria:**
- [ ] Follow-ups only appear after confirmation
- [ ] AI follow-ups for responses >100 chars
- [ ] Related questions clickable
- [ ] Navigation smooth scrolls with highlight animation
- [ ] "💡 Suggest" button works for partial answers

---

## 13. Stakeholder Views

### EVAL-067: List Stakeholder Profiles
**Priority:** High
**Endpoint:** `GET /api/stakeholder/profiles`

```bash
curl "$API_URL/api/stakeholder/profiles"
```

**Pass Criteria:**
- [ ] Returns 5 profiles: engineering (⚙️), design (🎨), leadership (👔), qa (🧪), marketing (📣)
- [ ] Each has: id, name, icon, focus_areas

---

### EVAL-068: Get Filtered View
**Priority:** High
**Endpoint:** `GET /api/stakeholder/view/{project_id}/{role}`

```bash
ROLE="engineering"
curl "$API_URL/api/stakeholder/view/$PROJECT_ID/$ROLE"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] content filtered for role
- [ ] profile info included
- [ ] Irrelevant sections removed

**Engineering Should Include:**
- Technical Requirements
- System Architecture
- API Specifications
- Performance Requirements

**Engineering Should Exclude:**
- Market Analysis
- Business Goals

---

### EVAL-069: Generate Role Summary
**Priority:** Medium
**Endpoint:** `POST /api/stakeholder/summary/{project_id}/{role}`

```bash
curl -X POST "$API_URL/api/stakeholder/summary/$PROJECT_ID/$ROLE"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] summary in markdown format
- [ ] Focused on role-specific concerns
- [ ] 500-800 words
- [ ] Clear sections and actionable items

---

### EVAL-070: Test All Roles
**Priority:** High
**Test:** Verify each role filters correctly

```bash
for ROLE in engineering design leadership qa marketing; do
  echo "Testing $ROLE..."
  curl "$API_URL/api/stakeholder/view/$PROJECT_ID/$ROLE" | jq '.profile.name'
done
```

**Pass Criteria:**
- [ ] All 5 roles return unique filtered content
- [ ] No errors for any role
- [ ] Focus areas match role

---

### EVAL-071: UI Role Selector
**UI Test:**
1. Generate PRD
2. Click "👥 Stakeholder Views"
3. Select each role
4. Verify filtered content
5. Click "✨ Generate Summary"
6. Verify role-specific summary
7. Test "📋 Copy" button

**Pass Criteria:**
- [ ] All 5 roles selectable
- [ ] Content changes per role
- [ ] Focus areas display correctly
- [ ] Summary generation works
- [ ] Copy to clipboard functional

---

## 14. AI Improvement Loop

### EVAL-072: Submit PRD Rating
**Priority:** High
**Endpoint:** `POST /api/feedback/rate/{project_id}`

```bash
curl -X POST "$API_URL/api/feedback/rate/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 3,
    "feedback_text": "Technical section lacks detail",
    "section_name": "Technical Requirements"
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Feedback saved with timestamp
- [ ] Rating between 1-5

---

### EVAL-073: Get Feedback Stats
**Priority:** High
**Endpoint:** `GET /api/feedback/stats/{project_id}`

```bash
curl "$API_URL/api/feedback/stats/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] Returns: total_feedback, average_rating, rating_distribution
- [ ] patterns object with: low_rated_sections, common_issues, improvement_areas

---

### EVAL-074: Get AI Improvement Suggestions
**Priority:** High
**Endpoint:** `GET /api/feedback/suggestions/{project_id}`

```bash
curl "$API_URL/api/feedback/suggestions/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] priority_improvements array (3-5 items)
- [ ] section_recommendations object
- [ ] rewrite_suggestions array
- [ ] missing_elements array

---

### EVAL-075: Apply AI Improvements
**Priority:** Critical
**Endpoint:** `POST /api/feedback/improve/{project_id}`

```bash
curl -X POST "$API_URL/api/feedback/improve/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] PRD content updated
- [ ] Previous version saved as snapshot
- [ ] Feedback incorporated
- [ ] Version number incremented

---

### EVAL-076: Question Feedback
**Priority:** Medium
**Endpoint:** `POST /api/feedback/question/{project_id}/{question_id}`

```bash
curl -X POST "$API_URL/api/feedback/question/$PROJECT_ID/$QUESTION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "was_helpful": true,
    "feedback_text": "AI suggestion was accurate"
  }'
```

**Pass Criteria:**
- [ ] Status 201
- [ ] Feedback linked to question
- [ ] Metadata stored (was_helpful)

---

### EVAL-077: Feedback Patterns
**Priority:** Medium
**Test:** Verify pattern detection

**Setup:** Submit multiple feedback items with keywords:
- "unclear" (x3)
- "missing" (x2)
- "too long" (x1)

**Expected Patterns:**
```json
{
  "common_issues": {
    "Clarity issues": 3,
    "Missing information": 2,
    "Too verbose": 1
  },
  "improvement_areas": [
    "Focus on clearer, more specific language",
    "Ensure comprehensive coverage of all topics"
  ]
}
```

**Pass Criteria:**
- [ ] Issues ranked by frequency
- [ ] Improvement areas generated
- [ ] Low-rated sections identified

---

## 15. Analytics & Insights

### EVAL-078: Overview Analytics
**Priority:** High
**Endpoint:** `GET /api/analytics/overview`

```bash
curl "$API_URL/api/analytics/overview"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] summary object with: total_projects, prds_generated, total_context_files, total_responses
- [ ] recent_activity (last 7 days)
- [ ] averages per project
- [ ] efficiency metrics

---

### EVAL-079: Project Analytics
**Priority:** Critical
**Endpoint:** `GET /api/analytics/project/{project_id}`

```bash
curl "$API_URL/api/analytics/project/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] project_info with time_spent_hours
- [ ] completion object with percentage and stages
- [ ] context, features, questions, prd stats
- [ ] feedback summary

**Stages Tracked:**
1. context_uploaded
2. features_extracted
3. questions_confirmed
4. prd_generated
5. feedback_provided

---

### EVAL-080: Project Timeline
**Priority:** Medium
**Endpoint:** `GET /api/analytics/timeline/{project_id}`

```bash
curl "$API_URL/api/analytics/timeline/$PROJECT_ID"
```

**Pass Criteria:**
- [ ] Status 200
- [ ] timeline array ordered by timestamp
- [ ] Event types: project_created, context_uploaded, features_extracted, prd_generated
- [ ] Each event has: type, timestamp, description

---

### EVAL-081: Time Tracking
**Priority:** Medium
**Test:** Verify time estimation

**Setup:**
1. Create project
2. Wait 30 seconds
3. Update project
4. Check analytics

**Pass Criteria:**
- [ ] time_spent_hours calculated
- [ ] Capped at 8 hours max
- [ ] Based on created_at to updated_at delta

---

### EVAL-082: Efficiency Metrics
**Priority:** Medium
**Test:** Calculate AI assistance and confirmation rates

**Setup:**
- Total responses: 100
- AI suggested: 75
- Confirmed: 60

**Expected:**
```json
{
  "ai_assistance_rate": 75.0,
  "confirmation_rate": 60.0
}
```

**Pass Criteria:**
- [ ] Rates calculated correctly
- [ ] Percentages rounded to 1 decimal

---

### EVAL-083: UI Analytics Dashboard
**UI Test:**
1. Click "📊 Analytics" in header
2. View Overview tab
3. Check all stat cards populated
4. Verify efficiency metrics
5. Switch to "📈 Current Project" tab
6. Review completion progress
7. Check timeline visualization

**Pass Criteria:**
- [ ] Modal opens on click
- [ ] Overview shows global stats
- [ ] Project view shows detailed metrics
- [ ] Completion percentage accurate
- [ ] Timeline events in order
- [ ] Charts and progress bars render
- [ ] Close button works

---

## 16. Frontend UI Tests

### EVAL-084: App Loads
**Priority:** Critical
**URL:** `https://pm-clarity.vercel.app`

**Pass Criteria:**
- [ ] Page loads without errors
- [ ] "PM Clarity" header visible
- [ ] Project selector visible
- [ ] Tab navigation visible

---

### EVAL-085: Create Project (UI)
**Priority:** Critical

**Steps:**
1. Click "+ New Project"
2. Enter project name
3. Click "Create Project"

**Pass Criteria:**
- [ ] Modal opens
- [ ] Project is created
- [ ] Project appears in dropdown
- [ ] Redirects to Context tab

---

### EVAL-086: Upload Context File (UI)
**Priority:** Critical

**Steps:**
1. Go to Context tab
2. Drag/drop or click to upload file
3. Wait for processing

**Pass Criteria:**
- [ ] File uploads successfully
- [ ] Progress indicator shown
- [ ] File appears in list
- [ ] Text extraction shown

---

### EVAL-087: Extract Features (UI)
**Priority:** Critical

**Steps:**
1. Go to Features tab
2. Click "Extract Features from Context"
3. Wait for AI processing

**Pass Criteria:**
- [ ] Loading state shown
- [ ] Features appear after processing
- [ ] Features have name and description
- [ ] Checkboxes work for selection

---

### EVAL-088: AI Prefill Questions (UI)
**Priority:** Critical

**Steps:**
1. Go to Questions tab
2. Click "AI Prefill from Context"
3. Wait for AI processing

**Pass Criteria:**
- [ ] Loading state shown
- [ ] Questions are populated with answers
- [ ] AI-suggested indicator visible
- [ ] Confirm buttons work

---

### EVAL-089: Generate PRD (UI)
**Priority:** Critical

**Steps:**
1. Confirm at least some question responses
2. Go to PRD tab
3. Click "Generate PRD"
4. Wait for generation

**Pass Criteria:**
- [ ] Loading state shown
- [ ] PRD content displayed
- [ ] PRD sections visible
- [ ] Export buttons work

---

### EVAL-090: Project Switching
**Priority:** High

**Steps:**
1. Create/select Project A
2. Add data to Project A
3. Switch to Project B
4. Verify data is different

**Pass Criteria:**
- [ ] Project selector works
- [ ] Data reloads for new project
- [ ] No stale data from previous project
- [ ] Tabs reset appropriately

---

### EVAL-091: Error Handling (UI)
**Priority:** High

**Steps:**
1. Try operations that might fail
2. Check error display

**Pass Criteria:**
- [ ] Network errors show toast
- [ ] Validation errors show inline
- [ ] UI doesn't crash on errors
- [ ] User can retry operations

---

## 17. Data Consistency Tests

### EVAL-092: Project Has Context But No Features
**Priority:** High
**Scenario:** Project with context files but features not extracted

**Steps:**
1. Create new project
2. Upload context files
3. Do NOT extract features
4. Go to Features tab

**Pass Criteria:**
- [ ] Features tab shows empty state
- [ ] "No Context Files" warning NOT shown (context exists)
- [ ] "Extract with AI" button is enabled
- [ ] Prompt suggests extracting features

---

### EVAL-093: Project Has Features But Missing Context
**Priority:** High
**Scenario:** Context files deleted after features extracted

**Steps:**
1. Create project with context
2. Extract features
3. Delete all context files
4. Verify features still exist

**Pass Criteria:**
- [ ] Features remain after context deletion
- [ ] Warning shown in Context tab about no files
- [ ] Questions tab still works with existing features
- [ ] No data corruption

---

### EVAL-094: Project Has Responses But No Features
**Priority:** High
**Scenario:** AI prefilled questions, then features deleted

**Steps:**
1. Create complete project (context + features + responses)
2. Delete all features
3. Go to Questions tab

**Pass Criteria:**
- [ ] Question responses still visible
- [ ] No UI crashes
- [ ] Features tab shows "No active features"
- [ ] PRD can still use existing responses

---

### EVAL-095: Switching Projects Resets Data
**Priority:** Critical
**Scenario:** Verify no data leakage between projects

**Steps:**
1. Select Project A with lots of data
2. Switch to Project B (new/empty project)
3. Verify all tabs

**Pass Criteria:**
- [ ] Context tab shows Project B's files (or empty)
- [ ] Features tab shows Project B's features (or empty)
- [ ] Questions tab shows Project B's responses (or empty)
- [ ] PRD tab shows Project B's PRD (or empty)
- [ ] No data from Project A visible

---

### EVAL-096: Rapid Project Switching
**Priority:** High
**Scenario:** Quickly switch between projects multiple times

**Steps:**
1. Switch to Project A
2. Immediately switch to Project B
3. Immediately switch to Project C
4. Verify data shown is for Project C

**Pass Criteria:**
- [ ] Final data matches selected project
- [ ] No stale data shown
- [ ] No console errors
- [ ] UI remains responsive

---

### EVAL-097: Stats Accuracy After Operations
**Priority:** Critical
**Scenario:** Verify stats update after each operation

**Steps:**
1. Note initial stats (confirmed count)
2. Confirm a response
3. Check stats endpoint
4. Unconfirm the response
5. Check stats again

**Pass Criteria:**
- [ ] Stats increase after confirm
- [ ] Stats decrease after unconfirm
- [ ] Percentage calculated correctly
- [ ] Stats match actual response count

```bash
curl -s https://pm-clarity.vercel.app/api/questions/stats/{PROJECT_ID}
curl -s https://pm-clarity.vercel.app/api/questions/responses/{PROJECT_ID} | jq '[.[] | select(.confirmed==true)] | length'
```

---

### EVAL-098: Features Sync with API
**Priority:** High
**Scenario:** Verify frontend features match backend

**Steps:**
1. Get features from API
2. Check features in UI
3. Toggle feature selection in UI
4. Verify API reflects change

**Pass Criteria:**
- [ ] Feature count matches
- [ ] Selection state matches
- [ ] Changes persist after refresh
- [ ] Order consistent

```bash
curl -s https://pm-clarity.vercel.app/api/features/{PROJECT_ID} | jq 'length'
```

---

### EVAL-099: Context Text Aggregation
**Priority:** High
**Scenario:** Verify aggregated text includes all files

**Steps:**
1. Upload File A with known text
2. Upload File B with different text
3. Get aggregated text
4. Verify both contents present

**Pass Criteria:**
- [ ] Aggregated text contains File A content
- [ ] Aggregated text contains File B content
- [ ] File names appear as separators
- [ ] No content truncation

```bash
curl -s https://pm-clarity.vercel.app/api/context/text/{PROJECT_ID}
```

---

## 18. User Guidance Tests

### EVAL-100: PRD Tab - Critical Warning (<20% confirmed)
**Priority:** Critical
**Scenario:** User has very few confirmations

**Steps:**
1. Create project with AI-prefilled questions
2. Confirm fewer than 20% of responses
3. Go to PRD tab

**Pass Criteria:**
- [ ] Red "Critical" warning banner shown
- [ ] Message mentions limited data
- [ ] "Review Questions" button present
- [ ] Button navigates to Questions tab

---

### EVAL-101: PRD Tab - Warning (20-50% confirmed)
**Priority:** High
**Scenario:** User has moderate confirmations

**Steps:**
1. Confirm 20-50% of responses
2. Go to PRD tab

**Pass Criteria:**
- [ ] Orange "Warning" banner shown
- [ ] Message mentions gaps
- [ ] "Confirm More" button present

---

### EVAL-102: PRD Tab - Info (50-80% confirmed)
**Priority:** Medium
**Scenario:** User has good confirmations

**Steps:**
1. Confirm 50-80% of responses
2. Go to PRD tab

**Pass Criteria:**
- [ ] Blue "Good Progress" info banner shown
- [ ] Encourages more confirmations optionally

---

### EVAL-103: PRD Tab - No Context Warning
**Priority:** Critical
**Scenario:** No context files uploaded

**Steps:**
1. Create new project
2. Go directly to PRD tab without uploading context

**Pass Criteria:**
- [ ] "No Context Files" warning shown
- [ ] "Upload Context" button present
- [ ] Button navigates to Context tab

---

### EVAL-104: PRD Tab - No Features Warning
**Priority:** High
**Scenario:** All features in parking lot

**Steps:**
1. Create project with context and features
2. Move all features to parking lot (deselect)
3. Go to PRD tab

**Pass Criteria:**
- [ ] "No Features Selected" warning shown
- [ ] "Select Features" button present
- [ ] Button navigates to Features tab

---

### EVAL-105: Project Bar Shows Current Project
**Priority:** Critical
**Scenario:** Verify user always knows which project they're working on

**Steps:**
1. Select Project A
2. Navigate through all tabs
3. Check header on each tab

**Pass Criteria:**
- [ ] Project bar visible on all tabs
- [ ] "Working on: [Project Name]" shown
- [ ] Project dropdown works
- [ ] Switching projects updates data

---

## 19. Edge Cases & Error Handling

### EVAL-106: API Timeout Handling
**Priority:** High
**Scenario:** AI operation takes too long

**Steps:**
1. Upload large context document
2. Trigger AI prefill
3. Wait for timeout or completion

**Pass Criteria:**
- [ ] Loading state shown throughout
- [ ] If timeout: error message displayed
- [ ] If timeout: user can retry
- [ ] No partial/corrupted data

---

### EVAL-107: Concurrent Operations
**Priority:** Medium
**Scenario:** User performs multiple operations quickly

**Steps:**
1. Click "AI Prefill" button
2. While loading, try other operations
3. Observe behavior

**Pass Criteria:**
- [ ] UI prevents conflicting operations
- [ ] Or handles them gracefully
- [ ] No data corruption
- [ ] Clear feedback to user

---

### EVAL-108: Large File Upload
**Priority:** High
**Scenario:** Upload file at size limit

**Steps:**
1. Create file near size limit (e.g., 4.5MB for 5MB limit)
2. Upload file
3. Verify processing

**Pass Criteria:**
- [ ] File uploads successfully
- [ ] Text extracted correctly
- [ ] No timeout during upload
- [ ] Error shown if over limit

---

### EVAL-109: Special Characters in Project Name
**Priority:** Medium
**Scenario:** Project name with special characters

**Steps:**
1. Create project with name: "Test Project (2026) - V2.0!"
2. Use project normally

**Pass Criteria:**
- [ ] Project creates successfully
- [ ] Name displays correctly
- [ ] Export filename is sanitized
- [ ] No URL encoding issues

---

### EVAL-110: Empty Response Handling
**Priority:** High
**Scenario:** API returns empty arrays/objects

**Steps:**
1. Create new project
2. Fetch features (should be empty)
3. Fetch responses (should be empty)
4. Verify UI

**Pass Criteria:**
- [ ] No console errors for empty arrays
- [ ] Empty states shown appropriately
- [ ] Buttons still functional
- [ ] User guided to next step

---

## 20. Integration Tests

### EVAL-111: Full Feature Workflow
**Priority:** Critical
**End-to-End Test:**

1. **Create Project with Template**
   - Select "Technical Spec" template
   - Verify project created

2. **Upload Context & Analyze**
   - Upload technical doc
   - Get quality score
   - Review coverage

3. **Extract Features**
   - AI extraction
   - Select key features

4. **Answer Questions with Follow-Ups**
   - AI prefill
   - Confirm answers with competitors mentioned
   - Verify follow-up questions appear
   - Answer follow-ups

5. **Generate PRD**
   - Create initial PRD
   - Verify content

6. **Edit & Version**
   - Edit section
   - Save named version
   - Compare versions

7. **Get Stakeholder Views**
   - View as Engineering
   - Generate summary
   - View as Design

8. **Share & Comment**
   - Create share link
   - Access via link
   - Add comment

9. **Provide Feedback**
   - Rate PRD (3 stars)
   - Add feedback text
   - Get improvement suggestions
   - Apply improvements

10. **View Analytics**
    - Check project analytics
    - Verify timeline
    - Review efficiency metrics

**Pass Criteria:** All steps complete without errors

---

### EVAL-112: Template + Adaptive Questions Integration
**Priority:** Medium
**Test:** Custom template affects question flow

1. Create template with custom sections
2. Create project with template
3. Answer questions
4. Verify follow-ups align with template structure

---

### EVAL-113: Context Analysis + Question Suggestions
**Priority:** Medium
**Test:** Context quality affects AI suggestions

1. Upload high-quality context (score >80)
2. Request smart suggestion
3. Verify high confidence

4. Remove context (score <40)
5. Request smart suggestion
6. Verify lower confidence

---

### EVAL-114: Feedback + Analytics Loop
**Priority:** Medium
**Test:** Feedback appears in analytics

1. Submit 5 pieces of feedback
2. Check feedback stats
3. Verify reflected in project analytics
4. Check patterns detected

---

### EVAL-115: Version History + Stakeholder Views
**Priority:** Medium
**Test:** Stakeholder views work across versions

1. Generate PRD v1
2. Create stakeholder view
3. Edit PRD → v2
4. Verify stakeholder view updates
5. Restore v1
6. Verify stakeholder view reflects v1

---

## Automated Test Script

Save as `run_evals.sh`:

```bash
#!/bin/bash
# PM Clarity Comprehensive Evaluation Script
# Usage: ./run_evals.sh [base_url]

BASE_URL="${1:-https://pm-clarity.vercel.app}"
PASS=0
FAIL=0
SKIP=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_status=$4
    local data=$5

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    status=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $name (HTTP $status)"
        ((PASS++))
    else
        echo -e "${RED}✗ FAIL${NC} - $name (Expected $expected_status, got $status)"
        echo "  Response: $body"
        ((FAIL++))
    fi
}

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         PM Clarity Comprehensive Evaluation Suite        ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Base URL: $BASE_URL"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# API Health
echo "━━━ 1. API Health ━━━"
test_endpoint "EVAL-001: Health Endpoint" "GET" "/api/health" 200
echo ""

# Projects
echo "━━━ 2. Projects API ━━━"
test_endpoint "EVAL-003: List Projects" "GET" "/api/projects" 200

# Create test project
echo "Creating test project..."
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/projects" \
    -H "Content-Type: application/json" \
    -d '{"name": "Eval Test Project"}')
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$PROJECT_ID" ]; then
    echo -e "${GREEN}✓ PASS${NC} - EVAL-004: Create Project (ID: $PROJECT_ID)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} - EVAL-004: Create Project"
    ((FAIL++))
fi

test_endpoint "EVAL-005: Create Project Validation" "POST" "/api/projects" 400 '{"name": ""}'
echo ""

# Context
echo "━━━ 3. Context API ━━━"
test_endpoint "EVAL-008: List Context Files" "GET" "/api/context/$PROJECT_ID" 200
test_endpoint "EVAL-011: Get Aggregated Text" "GET" "/api/context/text/$PROJECT_ID" 200
echo ""

# Features
echo "━━━ 4. Features API ━━━"
test_endpoint "EVAL-014: List Features" "GET" "/api/features/$PROJECT_ID" 200
test_endpoint "EVAL-016: Extract Features (No Context)" "POST" "/api/features/extract/$PROJECT_ID" 400
echo ""

# Questions
echo "━━━ 5. Questions API ━━━"
test_endpoint "EVAL-021: Get Questions" "GET" "/api/questions" 200
test_endpoint "EVAL-022: Get Responses" "GET" "/api/questions/responses/$PROJECT_ID" 200
test_endpoint "EVAL-027: Get Stats" "GET" "/api/questions/stats/$PROJECT_ID" 200
echo ""

# PRD
echo "━━━ 6. PRD API ━━━"
test_endpoint "EVAL-030: Generate PRD (No Responses)" "POST" "/api/prd/generate/$PROJECT_ID" 400
echo ""

# Advanced Features
echo "━━━ 7-15. Advanced Features ━━━"
test_endpoint "EVAL-039: List Templates" "GET" "/api/templates" 200
test_endpoint "EVAL-067: Stakeholder Profiles" "GET" "/api/stakeholder/profiles" 200
test_endpoint "EVAL-078: Overview Analytics" "GET" "/api/analytics/overview" 200
test_endpoint "EVAL-079: Project Analytics" "GET" "/api/analytics/project/$PROJECT_ID" 200
test_endpoint "EVAL-080: Project Timeline" "GET" "/api/analytics/timeline/$PROJECT_ID" 200
echo ""

# Cleanup
echo "━━━ Cleanup ━━━"
if [ -n "$PROJECT_ID" ]; then
    test_endpoint "EVAL-007: Delete Project" "DELETE" "/api/projects/$PROJECT_ID" 200
fi
echo ""

# Summary
TOTAL=$((PASS + FAIL + SKIP))
PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASS/$TOTAL)*100}")

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                      RESULTS SUMMARY                      ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo -e "║  ${GREEN}PASSED:  $PASS${NC}"
echo -e "║  ${RED}FAILED:  $FAIL${NC}"
echo -e "║  ${YELLOW}SKIPPED: $SKIP${NC}"
echo "║  PASS RATE: $PASS_RATE%"
echo "╚═══════════════════════════════════════════════════════════╝"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! Ready for deployment.${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Review output above.${NC}\n"
    exit 1
fi
```

Make executable:
```bash
chmod +x run_evals.sh
```

Run tests:
```bash
# Against production
./run_evals.sh

# Against staging
./run_evals.sh https://staging-pm-clarity.vercel.app

# Against local dev
./run_evals.sh http://localhost:5001
```

---

## Test Data Templates

### Sample Context Document
```markdown
# Product Vision: TaskFlow Pro

## Overview
TaskFlow Pro is a project management tool competing with Asana and Monday.com.

## Timeline
Launch Q2 2026, MVP by April 30, 2026.

## Metrics
- Target: 10,000 MAU by Q3
- Conversion rate: 5%
- Retention: 75%

## Users
- Small teams (5-15 people)
- Startups and agencies
- Tech-savvy project managers

## Technical
- REST API
- PostgreSQL database
- React frontend
- Integration with Slack and GitHub
```

### Sample Feedback
```json
{
  "rating": 3,
  "feedback_text": "The technical requirements section is too vague. Need more details on API endpoints, database schema, and authentication flow.",
  "section_name": "Technical Requirements"
}
```

---

## Pre-Deployment Checklist

### Code Review
- [ ] All code changes reviewed
- [ ] No console errors in development
- [ ] Environment variables configured
- [ ] Database migrations ready

### Build & Deploy
- [ ] Build succeeds locally
- [ ] No TypeScript/lint errors
- [ ] All serverless functions under 12 limit
- [ ] Runtime logs clean

### Testing
- [ ] Run automated test script
- [ ] All critical tests pass (83/83)
- [ ] Manually verify UI flows
- [ ] Test in production-like environment

### Documentation
- [ ] DEVELOPMENT_LOG.md updated
- [ ] EVALS.md reflects current features
- [ ] README.md accurate
- [ ] API endpoints documented

---

## Sign-Off Template

**Deployment Sign-Off**

- Date: _______________
- Tester: _______________
- Version: _______________
- Environment: _______________

**Test Results:**
- Automated Tests: _____/115 passed
- Critical Tests: _____/83 passed
- Manual UI Tests: Pass / Fail
- All Blockers Resolved: Yes / No

**Approval:**
- [ ] All critical tests passed
- [ ] No known blockers
- [ ] Ready for production

Signed: _______________

---

## Known Issues

| Issue | Severity | Status | Workaround |
|-------|----------|--------|------------|
| AI prefill timeout for very large context | Medium | Mitigated | Increased timeout to 300s, batch size 50 |
| | | | |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-23 | 1.0 | Initial core features evaluation suite |
| 2026-01-23 | 2.0 | Added advanced features tests (55 tests) |
| 2026-01-23 | 3.0 | Consolidated into single comprehensive suite (115 tests) |
