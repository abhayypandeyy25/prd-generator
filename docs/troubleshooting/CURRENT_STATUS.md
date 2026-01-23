# Current Status - PM Clarity Bug Fixes

**Last Updated**: January 23, 2026 @ 10:58 PM

---

## 🟢 Fixed Issues

### ✅ 1. Templates Database Tables Created
- **Status**: ✅ RESOLVED
- **Evidence**: API returns 5 templates successfully
- **Test**: `curl https://pm-clarity.vercel.app/api/templates` returns all templates
- **Action Taken**: SQL migration was run successfully in Supabase

### ✅ 2. Button Styling Fixed
- **Status**: ✅ DEPLOYED (pending verification)
- **Issue**: "Use This Template" button had white text on hover
- **Fix**: Added `color: white` to `.btn-primary:hover` in TemplateSelector.vue
- **Commit**: cf97fcc

---

## 🟡 Partially Fixed Issues

### ⚠️ 3. Template Preview Modal Empty
- **Status**: 🟡 DEPLOYED FIX (waiting for Vercel deployment)
- **Issue**: Clicking template shows "SECTIONS" but no section list
- **Root Cause**: `/api/templates/{id}` route was returning HTML instead of JSON
- **Fix Applied**:
  - Moved templates routes to top of vercel.json
  - Added explicit route for `/api/templates/(...)`
- **Commit**: cf97fcc
- **Wait Time**: ~2-5 minutes for Vercel deployment
- **Test**: After deployment, open modal and check if sections appear

---

## 🔴 Unresolved Issues

### ❌ 4. Question Extraction Still Stuck at 129
- **Status**: 🔴 NEEDS INVESTIGATION
- **Symptom**: Progress shows "129 / 139" and stops
- **Expected**: Should reach 139/139 in 2-4 minutes

#### What We've Tried
1. ✅ Increased axios timeout to 5 minutes
2. ✅ Reduced batch size from 50 to 30
3. ✅ Verified `maxDuration: 300` in vercel.json

#### Why It's Still Failing - Investigation Needed

**Possible Causes:**

1. **Vercel Function Timeout (Most Likely)**
   - Hobby plan has 10-second timeout for serverless functions
   - Pro plan needed for 300-second timeout
   - Our `maxDuration: 300` may not apply to Hobby plan

2. **Client-Side Progress Simulation**
   - Frontend simulates progress but stops at 129
   - May be a hardcoded limit or calculation error
   - Check QuestionsTab.vue line 173-179

3. **Actual Processing Failure**
   - AI processing might be failing after batch 4
   - Need to check server logs
   - 139 questions ÷ 30 batch = 5 batches
   - 129 = 4 complete batches + some of batch 5

4. **Network/Connection Issue**
   - Long-running request might be dropped
   - Need streaming/chunked response instead

#### Immediate Debug Steps

1. **Check Frontend Progress Logic**:
   ```javascript
   // In QuestionsTab.vue lines 167-182
   const simulateProgress = () => {
     const totalQuestions = store.stats.total_questions || 139
     prefillProgress.value = { processed: 0, total: totalQuestions }

     progressInterval = setInterval(() => {
       if (prefillProgress.value.processed < totalQuestions - 10) {  // <-- SUSPICIOUS!
         // Stops at 129 (139 - 10)
         const increment = Math.floor(Math.random() * 8) + 3
         prefillProgress.value.processed = Math.min(
           prefillProgress.value.processed + increment,
           totalQuestions - 10  // <-- BUG HERE?
         )
       }
     }, 800)
   }
   ```

   **FOUND THE BUG!** Line 173 and 178: `totalQuestions - 10` = 129
   This is intentional to prevent simulation from completing before API, but it looks stuck!

2. **Check API Response**:
   - Open browser DevTools > Network tab
   - Click "AI Prefill from Context"
   - Watch for `/api/questions/prefill/{projectId}` request
   - Check if it completes or times out
   - Check response status and data

3. **Verify Vercel Plan**:
   ```bash
   vercel whoami
   vercel inspect pm-clarity --url
   ```
   Check if on Hobby plan (10s timeout) or Pro plan (300s timeout)

---

## 🎯 Next Steps

### For Template Preview Modal
1. Wait 5 minutes for deployment
2. Hard refresh browser (Cmd+Shift+R)
3. Test template preview modal
4. If still broken, check browser console for errors

### For Question Extraction Bug

#### Option A: Quick UI Fix (Recommended)
Fix the progress simulation to reach 139:

```javascript
// Change in QuestionsTab.vue line 173 & 178
if (prefillProgress.value.processed < totalQuestions - 1) {  // Was: totalQuestions - 10
  const increment = Math.floor(Math.random() * 8) + 3
  prefillProgress.value.processed = Math.min(
    prefillProgress.value.processed + increment,
    totalQuestions - 1  // Was: totalQuestions - 10
  )
}
```

**This won't fix the actual timeout, but will make progress reach 139.**

#### Option B: Investigate Actual Timeout (Thorough)
1. Check Vercel deployment plan and function duration limits
2. Add server-side logging to track which batch fails
3. Test with smaller project (fewer questions)
4. Consider upgrading to Vercel Pro if on Hobby plan

#### Option C: Implement Streaming (Best Long-Term)
1. Change prefill to stream progress updates
2. Use Server-Sent Events (SSE) or polling
3. Process batches asynchronously
4. Update progress bar in real-time as each batch completes

---

## 📊 Testing Checklist

### After Next Deployment (ETA: ~5 min)

- [ ] **Template Preview Modal**
  - [ ] Click "+ New Project"
  - [ ] Click on "Lean PRD (Startup)" template
  - [ ] Verify modal shows 5 sections:
    - Problem Statement (Required)
    - Proposed Solution (Required)
    - Success Metrics (Required)
    - MVP Features (Required)
    - Timeline
  - [ ] Click "Use This Template"
  - [ ] Verify project creates successfully

- [ ] **Button Styling**
  - [ ] Hover over "Use This Template" button
  - [ ] Text should remain white (readable)

- [ ] **Question Extraction** (Needs further fix)
  - [ ] Create/open project
  - [ ] Upload context files
  - [ ] Select features
  - [ ] Click "AI Prefill from Context"
  - [ ] Watch progress counter
  - [ ] Note: Will likely still stop at 129
  - [ ] Check browser DevTools Network tab for actual API response

---

## 🔧 Files Modified

| File | Change | Status |
|------|--------|--------|
| [vercel.json](vercel.json) | Prioritized templates routes | ✅ Deployed |
| [frontend/src/components/TemplateSelector.vue](frontend/src/components/TemplateSelector.vue) | Fixed button hover color | ✅ Deployed |
| [migrations/002_templates_READY_TO_RUN.sql](migrations/002_templates_READY_TO_RUN.sql) | Ready-to-run migration file | ✅ Created |
| [frontend/src/components/QuestionsTab.vue](frontend/src/components/QuestionsTab.vue) | Progress simulation (BUG FOUND) | ❌ Needs fix |

---

## 💡 Recommended Action

1. **Wait 5 minutes** for current deployment to complete
2. **Test template preview modal** - should work now
3. **Fix question extraction bug** by either:
   - Quick fix: Change `totalQuestions - 10` to `totalQuestions - 1` in QuestionsTab.vue
   - Full investigation: Check Vercel plan, add logging, test API response time
4. **Monitor** browser console and network tab for errors

---

## 📞 Questions to Answer

1. **What Vercel plan are you on?** (Hobby vs Pro)
   - Hobby: 10-second serverless function timeout
   - Pro: Configurable up to 300 seconds

2. **Does the API request complete?**
   - Check DevTools Network tab
   - Look for `/api/questions/prefill/{projectId}`
   - Status 200 = success, 504 = timeout

3. **What's in the API response?**
   - How many responses returned?
   - Does it say "Saved X responses"?
   - Any error messages?

---

**Current Hypothesis**:
The progress simulation intentionally stops at 129 (totalQuestions - 10) to wait for API response. If API is timing out or slow, it looks stuck. Need to check if API actually completes and returns all 139 question answers.
