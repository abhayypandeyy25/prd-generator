# PM Clarity - Development Log

## 2026-01-23: Advanced Features Suite - 9 Major Features Added

### Summary
Implemented a comprehensive suite of 9 advanced features to transform PM Clarity into a full-featured PRD generation platform with collaboration, analytics, and continuous improvement capabilities.

### Features Implemented

#### **Feature 1: PRD Editing & Refinement** ✅
- **Backend**: `api/prd.py` - Added edit, history, restore, save-version, regenerate-section endpoints
- **Frontend**: `PRDEditor.vue` - Rich markdown editor with split view, version history panel
- **Database**: `migrations/001_prd_editing.sql` - Version tracking and snapshots
- **Key Capabilities**:
  - Real-time markdown editing with live preview
  - Version history with snapshots
  - Named version saves with change summaries
  - AI-powered section regeneration
  - Side-by-side diff view

#### **Feature 2: PRD Templates & Customization** ✅
- **Backend**: `api/templates.py` - Full CRUD API with clone functionality
- **Frontend**: `TemplateSelector.vue`, updated `App.vue` with multi-step project creation
- **Database**: `migrations/002_templates.sql` - Templates, sections, custom questions
- **Key Capabilities**:
  - 5 built-in templates (Lean PRD, Detailed PRD, Technical Spec, One-Pager, Feature Brief)
  - Custom template creation
  - Template cloning and modification
  - Section-level customization
  - Template preview before selection

#### **Feature 3: Collaboration & Sharing** ✅
- **Backend**: `api/share.py`, `api/comments.py` - Share links and threaded comments
- **Frontend**: `ShareModal.vue` - Share dialog with access controls
- **Database**: `migrations/003_collaboration.sql` - Shares, comments, activity, approvals
- **Key Capabilities**:
  - Shareable links with password protection
  - Access level controls (view-only, comment, edit)
  - Expiration dates
  - Threaded comment system with resolve/reply
  - Activity tracking

#### **Feature 4: Version History & Comparison** ✅
- **Backend**: `api/prd.py` - Compare, changelog, get_snapshot endpoints
- **Frontend**: Integrated into `PRDEditor.vue`
- **Key Capabilities**:
  - Full version history
  - Side-by-side version comparison
  - Automatic diff computation
  - Changelog generation between versions
  - One-click version restore

#### **Feature 5: Smart Context Analysis** ✅
- **Backend**: `api/context.py` - Analyze and summarize endpoints with AI analysis
- **Frontend**: `ContextAnalysis.vue` - Comprehensive analysis dashboard
- **Key Capabilities**:
  - Quality score (0-100) with breakdown
  - Coverage analysis for 8 categories (personas, metrics, technical, timeline, etc.)
  - Entity extraction (dates, percentages, monetary values, technical terms)
  - Conflict/contradiction detection
  - AI-powered deep analysis with key themes and risks
  - Per-file AI summarization

#### **Feature 6: Adaptive Questioning System** ✅
- **Backend**: `api/questions.py` - Follow-ups, save-follow-up, smart-suggest endpoints
- **Frontend**: `FollowUpQuestions.vue`, enhanced `QuestionCard.vue`
- **Key Capabilities**:
  - Rule-based follow-up questions (5 trigger types)
  - AI-generated contextual follow-ups
  - Skip logic to avoid irrelevant questions
  - Smart suggestions based on context and other responses
  - Related question navigation
  - Question highlighting and smooth scrolling

#### **Feature 8: Stakeholder View** ✅
- **Backend**: `api/stakeholder.py` - Role-based filtering and AI summaries
- **Frontend**: `StakeholderView.vue` - Role selector with customized views
- **Key Capabilities**:
  - 5 stakeholder profiles (Engineering, Design, Leadership, QA, Marketing)
  - Filtered content relevant to each role
  - AI-generated executive summaries per role
  - Focus areas highlighting
  - Copy/export stakeholder views

#### **Feature 9: AI Improvement Loop** ✅
- **Backend**: `api/feedback.py` - Rating, suggestions, improve endpoints
- **Frontend**: `FeedbackPanel.vue` - Integrated feedback system
- **Database**: `migrations/004_feedback.sql` - Feedback tracking
- **Key Capabilities**:
  - 5-star PRD rating system
  - Section-specific feedback
  - Feedback analytics with pattern detection
  - AI-powered improvement suggestions
  - One-click PRD improvement based on feedback
  - Feedback statistics and trends

#### **Feature 10: Analytics & Insights** ✅
- **Backend**: `api/analytics.py` - Overview, project, timeline endpoints
- **Frontend**: `AnalyticsDashboard.vue` - Comprehensive analytics dashboard
- **Key Capabilities**:
  - Overview analytics across all projects
  - Project-specific deep dive
  - Completion tracking with stage visualization
  - Time estimation
  - Efficiency metrics (AI assistance rate, confirmation rate)
  - Project timeline visualization
  - Context, features, questions, PRD statistics

### Files Created

**Backend APIs (9 new files)**:
- `api/stakeholder.py` - Stakeholder views with 5 profiles
- `api/feedback.py` - Feedback collection and AI improvements
- `api/analytics.py` - Usage analytics and insights
- `api/share.py` - Share link management (Feature 3)
- `api/comments.py` - Threaded comments (Feature 3)
- `api/templates.py` - Template CRUD (Feature 2)

**Database Migrations (4 new files)**:
- `migrations/001_prd_editing.sql` - Version tracking
- `migrations/002_templates.sql` - Templates system
- `migrations/003_collaboration.sql` - Sharing & comments
- `migrations/004_feedback.sql` - Feedback collection

**Frontend Components (8 new files)**:
- `ContextAnalysis.vue` - Smart context analysis dashboard
- `FollowUpQuestions.vue` - Adaptive follow-up questions
- `StakeholderView.vue` - Role-based PRD views
- `FeedbackPanel.vue` - Feedback and improvement system
- `AnalyticsDashboard.vue` - Analytics and insights
- `PRDEditor.vue` - Rich markdown editor (Feature 1)
- `ShareModal.vue` - Share dialog (Feature 3)
- `TemplateSelector.vue` - Template selection (Feature 2)

### Files Modified

**Backend**:
- `api/prd.py` - Added 10+ new endpoints for editing, versioning, comparison
- `api/context.py` - Added analysis and summarization with AI
- `api/questions.py` - Added adaptive questioning with 200+ lines of logic
- `vercel.json` - Added 3 new API routes

**Frontend**:
- `frontend/src/services/api.js` - Added 4 new API modules (30+ new endpoints)
- `frontend/src/components/PRDTab.vue` - Integrated stakeholder view and feedback
- `frontend/src/components/QuestionsTab.vue` - Added navigation handler
- `frontend/src/components/QuestionCard.vue` - Integrated follow-ups and smart suggestions
- `frontend/src/components/ContextTab.vue` - Added context analysis component
- `frontend/src/App.vue` - Added analytics modal

### Database Changes

**New Tables** (4):
- `prd_edit_snapshots` - Version history storage
- `prd_templates` - Template definitions
- `prd_shares` - Share links with access control
- `prd_feedback` - User feedback collection

**New Fields**:
- `generated_prds.version` - Version tracking
- `generated_prds.template_id` - Template reference
- Multiple metadata columns

### Technical Highlights

#### AI-Powered Features
- **Smart Context Analysis**: 8-category coverage scoring + entity extraction
- **Adaptive Questions**: Context-aware follow-ups and suggestions
- **Stakeholder Summaries**: Role-specific AI-generated executive summaries
- **Feedback Improvements**: AI analyzes feedback patterns and rewrites PRD

#### Advanced Algorithms
- **Diff Computation**: Python difflib for version comparison
- **Coverage Scoring**: Weighted keyword matching across categories
- **Skip Logic**: Conditional question flow based on responses
- **Time Estimation**: Delta-based time tracking with 8-hour caps
- **Pattern Detection**: Feedback analysis for improvement areas

#### User Experience
- **Progressive Disclosure**: Follow-ups only after confirmation
- **Contextual Help**: Smart suggestions based on other answers
- **Real-time Feedback**: Instant quality scores and suggestions
- **Role-Based Views**: Tailored content for different stakeholders
- **Visual Analytics**: Charts, timelines, and completion tracking

### API Endpoints Summary

**Total New Endpoints**: 40+

| Feature | Endpoints | Methods |
|---------|-----------|---------|
| PRD Editing | 8 | GET, PUT, POST |
| Templates | 6 | GET, POST, PUT, DELETE |
| Sharing | 4 | GET, POST, DELETE |
| Comments | 5 | GET, POST, DELETE |
| Context Analysis | 3 | GET, POST |
| Adaptive Questions | 3 | POST |
| Stakeholder Views | 3 | GET, POST |
| Feedback | 4 | GET, POST |
| Analytics | 3 | GET |

### Performance Optimizations
- Batch processing maintained at 50 questions
- 300s timeout for AI operations
- Caching for template and profile data
- Efficient SQL queries with proper indexing
- Frontend state management with Pinia

### Deployment
All features successfully deployed to: **https://pm-clarity.vercel.app**

Build stats:
- 110 modules transformed
- 71.25 KB CSS (gzipped: 10.84 KB)
- 250.92 KB JS (gzipped: 83.03 KB)
- 10 serverless functions

### Next Steps
1. Run updated evaluation suite (see EVALS.md updates)
2. Gather user feedback on new features
3. Monitor analytics for usage patterns
4. Consider: Export stakeholder views, Team collaboration features, API webhooks

---

## 2026-01-23: Removed Firebase Authentication & Created Evaluation Suite

### Summary
Removed all Firebase authentication from the application due to deployment errors, and created a comprehensive evaluation suite for pre-deployment testing.

### Problem
- Firebase authentication was causing "500 Server Error" and login page errors
- The `/opt/wrapper: does not exist` error was occurring with explicit Python runtime versions
- AI prefill was timing out due to processing 139 questions in 60 seconds

### Solutions

#### 1. Removed Authentication
Removed all Firebase auth code from backend and frontend to restore working state.

**Backend Files Modified:**
- `api/projects.py` - Removed auth imports and verification
- `api/context.py` - Removed auth verification
- `api/features.py` - Removed auth and ownership verification
- `api/questions.py` - Removed auth verification
- `api/prd.py` - Changed `verify_project_ownership` to simple `verify_project_exists`

**Frontend Files Modified:**
- `frontend/src/App.vue` - Removed auth guard, AuthPage, authStore imports, user menu
- `frontend/src/services/api.js` - Removed Firebase imports and auth token interceptors

#### 2. Fixed Python Runtime Issue
- Removed explicit Python runtime version from `vercel.json`
- Vercel now uses default Python 3.12 with uv package manager
- This resolved the `/opt/wrapper: does not exist` error

```json
// vercel.json - Before
"runtime": "@vercel/python@4.3.1"

// After (removed explicit runtime)
"functions": {
  "api/*.py": {
    "maxDuration": 300
  }
}
```

#### 3. Fixed AI Prefill Timeout
- Increased `maxDuration` from 60s to 300s in `vercel.json`
- Increased batch size from 25 to 50 questions per API call in `questions.py`

```python
# questions.py - Before
batch_size = 25

# After
batch_size = 50
```

### Evaluation Suite Created

Created comprehensive testing suite with 41 test cases:

**Files Created:**
- `EVALS.md` - Complete documentation with test cases, pass/fail criteria, curl commands
- `run_evals.sh` - Automated test script (25 automated tests)

**Test Categories:**
| Category | Tests |
|----------|-------|
| API Health | 2 |
| Projects | 5 |
| Context Files | 6 |
| Features | 7 |
| Questions | 8 |
| PRD | 5 |
| Frontend UI | 8 |
| **Total** | **41** |

**Usage:**
```bash
# Run all automated evals
./run_evals.sh

# Run against staging
./run_evals.sh https://staging.vercel.app
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║                      RESULTS SUMMARY                       ║
╠════════════════════════════════════════════════════════════╣
║  PASSED:  25                                              ║
║  FAILED:  0                                               ║
║  SKIPPED: 0                                               ║
║  PASS RATE: 100%                                          ║
╚════════════════════════════════════════════════════════════╝

✓ All tests passed! Ready for deployment.
```

### Deployment Verified
- All 25 automated API tests pass
- Application live at https://pm-clarity.vercel.app
- Core functionality restored without authentication

### Future: Re-adding Authentication
When ready to add authentication back:
1. Use lighter-weight auth (PyJWT instead of firebase-admin)
2. Ensure `user_id` column exists in Supabase `projects` table
3. Test thoroughly with evaluation suite before deployment

---

## 2026-01-22: Fix Duplicate Loading Animations on PRD Generation

### Problem
When generating a PRD, two loading indicators were showing simultaneously:
1. PRDTab's own loading indicator ("Generating your PRD with AI...")
2. Global loading overlay from App.vue ("Processing...")

### Solution
Separated PRD generation from the global loading state by:
1. Adding a local `isGenerating` ref in PRDTab.vue
2. Creating `generatePRDWithoutLoading()` method in the store that doesn't trigger global loading
3. Updating PRDTab to use its own loading state instead of `store.loading`

**Files Modified:**
- `frontend/src/components/PRDTab.vue` - Added local `isGenerating` state, updated template conditions
- `frontend/src/stores/projectStore.js` - Added `generatePRDWithoutLoading()` method

### Code Changes
```javascript
// PRDTab.vue
const isGenerating = ref(false)

const generatePRD = async () => {
  isGenerating.value = true
  try {
    await store.generatePRDWithoutLoading()
  } catch (error) {
    console.error('Failed to generate PRD:', error)
  } finally {
    isGenerating.value = false
  }
}
```

```javascript
// projectStore.js
async generatePRDWithoutLoading() {
  // Same as generatePRD but without setLoading() calls
  // Component handles its own loading state
}
```

---

## 2026-01-22: AI Prefill Progress Animation

### Summary
Added a visual progress animation when AI is prefilling questions, showing users the processing status in real-time.

### Changes

**Files Modified:**
- `frontend/src/components/QuestionsTab.vue` - Added progress overlay and animation

### Features
- Full-screen overlay with blur background during AI processing
- Animated spinner with pulsing counter
- Shows "X / 139 questions processed" with animated increment
- Progress bar fills as questions are processed
- Displays number of selected features being used
- Simulated progress animation while waiting for API response
- Final count shown before overlay closes

### Implementation Details
```vue
<div v-if="isPrefilling" class="ai-processing-overlay">
  <div class="ai-processing-card">
    <div class="ai-spinner"></div>
    <h3>AI is analyzing your context...</h3>
    <div class="ai-counter">
      <span class="counter-current">{{ prefillProgress.processed }}</span>
      <span class="counter-separator">/</span>
      <span class="counter-total">{{ prefillProgress.total }}</span>
    </div>
    <p>questions processed</p>
    <div class="ai-progress-bar">...</div>
    <p>Using context + {{ store.activeFeatureCount }} selected features</p>
  </div>
</div>
```

---

## 2026-01-22: AI Batch Processing for All Questions

### Summary
Updated the AI prefill to process ALL questions (not just first 30) by implementing batch processing.

### Problem
With 139 questions, the API was only processing the first 30 to avoid timeouts, leaving most questions unanswered.

### Solution
Implemented batch processing that:
1. Splits questions into batches of 25
2. Processes each batch sequentially
3. Continues even if one batch fails
4. Combines all responses

**Files Modified:**
- `api/questions.py` - Added `analyze_context_for_questions_batch()` function and updated main function to iterate through all questions

### Code Changes
```python
def analyze_context_for_questions(context, questions, selected_features=None):
    # Process questions in batches of 25 to avoid timeout
    batch_size = 25
    all_responses = []

    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        try:
            batch_responses = analyze_context_for_questions_batch(
                context, batch, selected_features, client
            )
            all_responses.extend(batch_responses)
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {e}")
            continue

    return all_responses
```

---

## 2026-01-22: Home Page with Projects & Parking Lot Sections

### Summary
Renamed "Projects" tab to "Home" and added a Parking Lot section showing deselected features across all projects.

### Changes

**Files Modified:**
- `frontend/src/App.vue` - Changed tab label from "Projects" to "Home"
- `frontend/src/components/ProjectsTab.vue` - Completely redesigned with two sections:
  1. **Projects Section** - Shows all projects with feature counts
  2. **Parking Lot Section** - Shows deselected features grouped by project

### New Features
- Home tab now shows both projects and parking lot
- Each project card shows feature count badge
- Parking Lot is collapsible (click header to toggle)
- Shows total parked features count
- Features grouped by project with AI badge indicator
- Fetches features for all projects on mount

### UI Structure
```
Home Tab
├── Projects Section
│   ├── Project cards with feature count
│   └── Open/Delete actions
└── Parking Lot Section (collapsible)
    ├── Project A
    │   └── Parked features list
    └── Project B
        └── Parked features list
```

---

## 2026-01-22: Features Tab Implementation

### Summary
Added a new "Features" tab between Context and Questions to extract and manage product features.

### New Workflow
```
Projects → Context → Features (NEW) → Questions → PRD
```

### Database Changes Required
Run this SQL in Supabase SQL Editor:
```sql
CREATE TABLE IF NOT EXISTS features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    is_selected BOOLEAN DEFAULT TRUE,
    is_ai_generated BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_features_project_id ON features(project_id);
ALTER TABLE features ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all on features" ON features FOR ALL USING (true) WITH CHECK (true);
```

### Files Created
- `api/features.py` - Backend API for feature extraction and management
- `frontend/src/components/FeaturesTab.vue` - Features tab component
- `frontend/src/components/FeatureCard.vue` - Reusable feature card component

### Files Modified
- `vercel.json` - Added features API routes
- `frontend/src/services/api.js` - Added featuresApi
- `frontend/src/stores/projectStore.js` - Added features state, getters, and actions
- `frontend/src/App.vue` - Added Features tab navigation (2. Features)
- `frontend/src/components/ContextTab.vue` - Changed "Continue to Questions" → "Continue to Features"
- `api/questions.py` - Updated prefill to include selected features in AI context

### Features
- Extract features from context using AI
- Add features manually
- Edit feature name and description
- Move features to/from Parking Lot (deselected features)
- Delete features
- Selected features inform AI when prefilling questions

### API Endpoints
- `GET /api/features/{project_id}` - List all features
- `POST /api/features/extract/{project_id}` - AI extraction
- `POST /api/features/{project_id}` - Create manual feature
- `PUT /api/features/item/{feature_id}` - Update feature
- `PUT /api/features/select/{feature_id}` - Toggle selection
- `DELETE /api/features/item/{feature_id}` - Delete feature

---

## 2026-01-22: Frontend Improvements - Projects Tab & New Project Flow

### Issue 1: New Project Not Resetting to Fresh State
**Problem:** When creating a new project, it was selecting the project but not resetting to a fresh home screen (context tab with empty state).

**Solution:** Added `resetProjectData()` method to store and called it in `createProject()`.

**Files Modified:**
- `frontend/src/stores/projectStore.js` - Added `resetProjectData()` method, called after project creation

### Issue 2: No Projects Overview Page
**Problem:** No way to see all projects at once or manage them from a single view.

**Solution:** Added a dedicated "Projects" tab with a grid view of all projects.

**Files Created:**
- `frontend/src/components/ProjectsTab.vue` - New component showing all projects in a grid layout

**Files Modified:**
- `frontend/src/App.vue` - Added ProjectsTab import, new tab navigation, and event handlers
- `frontend/src/stores/projectStore.js` - Added 'projects' to valid tab list

**New Features:**
- Projects tab showing all projects in a card grid
- Project cards show name, creation date, and actions
- Delete project with confirmation modal
- "Open Project" button navigates to context tab
- Empty state with call-to-action when no projects exist

---

## 2026-01-22: Claude Model ID Update

### Issue: AI Service Temporarily Unavailable
**Error:** `"AI service temporarily unavailable", "details": "Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'model: claude-3-5-sonnet-20241022'}"`

**Root Cause:** The model ID `claude-3-5-sonnet-20241022` is no longer available in the Anthropic API.

**Solution:** Updated model ID to `claude-sonnet-4-20250514` in both files:
- `api/questions.py` line 105
- `api/prd.py` line 151

**Files Modified:**
```python
# Before
model="claude-3-5-sonnet-20241022"

# After
model="claude-sonnet-4-20250514"
```

---

## 2026-01-21: Vercel Deployment - Function Consolidation

### Summary
Consolidated 19 serverless functions into 5 to fit Vercel Hobby plan limit (12 max).

### Issue: Vercel Hobby Plan Limit
**Error:** `No more than 12 Serverless Functions can be added to a Deployment on the Hobby plan`

**Solution:** Consolidated all serverless functions by using path-based routing within single handlers.

### New Consolidated Architecture

```
pm-clarity/api/
├── index.py       # Root + health endpoints
├── projects.py    # All project operations (list, create, get, delete)
├── context.py     # All context operations (list, upload, text, file delete)
├── questions.py   # All question operations (list, responses, prefill, confirm, stats)
├── prd.py         # All PRD operations (get, generate, preview, export md/docx)
└── data/
    └── questions.json
```

**Total: 5 serverless functions** (well under 12 limit)

### Updated vercel.json Routes

All routes now use path-based routing to consolidated handlers:
```json
{
  "routes": [
    { "src": "/api/context/(.*)", "dest": "/api/context.py" },
    { "src": "/api/questions/(.*)", "dest": "/api/questions.py" },
    { "src": "/api/questions$", "dest": "/api/questions.py" },
    { "src": "/api/prd/(.*)", "dest": "/api/prd.py" },
    { "src": "/api/projects/(.*)", "dest": "/api/projects.py" },
    { "src": "/api/projects$", "dest": "/api/projects.py" },
    { "src": "/api/health$", "dest": "/api/index.py" },
    { "src": "/api/index$", "dest": "/api/index.py" }
  ]
}
```

### Files Removed (replaced by consolidated handlers)
- `api/projects/[id].py`
- `api/context/[project_id].py`
- `api/context/upload/[project_id].py`
- `api/context/text/[project_id].py`
- `api/context/file/[file_id].py`
- `api/questions/responses/[project_id].py`
- `api/questions/response/[project_id]/[question_id].py`
- `api/questions/confirm/[project_id]/[question_id].py`
- `api/questions/stats/[project_id].py`
- `api/questions/prefill/[project_id].py`
- `api/prd/[project_id].py`
- `api/prd/generate/[project_id].py`
- `api/prd/preview/[project_id].py`
- `api/prd/export/md/[project_id].py`
- `api/prd/export/docx/[project_id].py`
- `api/health.py`

### How Path-Based Routing Works

Each consolidated handler parses the request path to determine the operation:

**context.py:**
- `/api/context/{project_id}` → list files
- `/api/context/upload/{project_id}` → upload files
- `/api/context/text/{project_id}` → get aggregated text
- `/api/context/file/{file_id}` → get/delete file

**questions.py:**
- `/api/questions` → list all questions
- `/api/questions/prefill/{project_id}` → AI prefill
- `/api/questions/responses/{project_id}` → get/save responses
- `/api/questions/response/{project_id}/{question_id}` → single response
- `/api/questions/confirm/{project_id}/{question_id}` → confirm response
- `/api/questions/stats/{project_id}` → get stats

**prd.py:**
- `/api/prd/{project_id}` → get PRD
- `/api/prd/generate/{project_id}` → generate PRD
- `/api/prd/preview/{project_id}` → preview with HTML
- `/api/prd/export/md/{project_id}` → export markdown
- `/api/prd/export/docx/{project_id}` → export Word

---

## 2026-01-21: Initial Vercel Deployment Fixes

### Issues Fixed

#### Issue 1: Wrong Database Table Name (CRITICAL)
**Problem:** API files used table name `prds` but Supabase schema defines `generated_prds`
**Solution:** Updated all references to use `generated_prds`

#### Issue 2: Missing Health Check Endpoint
**Problem:** No `/api/health` endpoint
**Solution:** Added to `index.py`

### Environment Variables (set in Vercel)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `ANTHROPIC_API_KEY` - Claude API key

### Database Schema (Supabase)
Tables:
- `projects` - Project metadata
- `context_files` - Uploaded documents with extracted text
- `question_responses` - User answers to PRD questions
- `generated_prds` - Generated PRD documents

### Deployment Commands
```bash
cd pm-clarity
vercel login
vercel link
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY
vercel env add ANTHROPIC_API_KEY
vercel --prod
```

### Verification Steps
1. `curl https://<app>.vercel.app/api/health` → `{"status": "ok"}`
2. `curl https://<app>.vercel.app/api/projects` → `[]` or list
3. Test full flow in browser

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `vercel.json` | Deployment config & routing |
| `api/index.py` | Root + health endpoints |
| `api/projects.py` | Project CRUD |
| `api/context.py` | File upload & management |
| `api/questions.py` | Questions & AI prefill (batch processing) |
| `api/prd.py` | PRD generation & export |
| `api/features.py` | Feature extraction & management |
| `api/data/questions.json` | Question definitions |
| `frontend/src/services/api.js` | Frontend API client |
| `frontend/src/stores/projectStore.js` | Pinia state management |
| `frontend/src/components/ProjectsTab.vue` | Home page with projects & parking lot |
| `frontend/src/components/FeaturesTab.vue` | Feature management UI |
| `frontend/src/components/FeatureCard.vue` | Individual feature card |
| `frontend/src/components/QuestionsTab.vue` | Questions with AI progress animation |
| `frontend/src/components/PRDTab.vue` | PRD generation with local loading state |
| `supabase_schema.sql` | Database schema |
| `EVALS.md` | Comprehensive evaluation test documentation |
| `run_evals.sh` | Automated API test script |

## Database Tables

| Table | Purpose |
|-------|---------|
| `projects` | Project metadata |
| `context_files` | Uploaded documents with extracted text |
| `features` | Product features (AI-extracted or manual) |
| `question_responses` | User answers to PRD questions |
| `generated_prds` | Generated PRD documents |

## Common Issues & Solutions

1. **Table not found** → Use `generated_prds` not `prds`
2. **CORS errors** → Check `cors_headers()` in handlers
3. **Path parsing** → Each handler has `parse_path()` function
4. **Timeout** → Max duration 300s in vercel.json, batch size 50 for questions
5. **Function limit** → Keep under 12 functions for Hobby plan
6. **AI service unavailable** → Check model ID is current (use `claude-sonnet-4-20250514`)
7. **Features table not found** → Run CREATE TABLE SQL in Supabase SQL Editor
8. **Duplicate loading animations** → Use component-local loading state instead of global `store.loading` for long-running operations
9. **`/opt/wrapper: does not exist`** → Remove explicit Python runtime version from vercel.json, let Vercel use default
10. **AI prefill timeout** → Increase maxDuration and batch size

## Application Flow

```
1. Home (Projects & Parking Lot)
   └── Create/Select Project

2. Context
   └── Upload documents (PDF, TXT, etc.)
   └── AI extracts text automatically

3. Features
   └── Click "Extract with AI" to analyze context
   └── Edit/add features manually
   └── Park features not needed (move to parking lot)

4. Questions
   └── Click "AI Prefill from Context"
   └── Progress animation shows processing status
   └── AI uses context + selected features
   └── Review and confirm answers

5. PRD
   └── Generate PRD document
   └── Export as Markdown or Word
```
