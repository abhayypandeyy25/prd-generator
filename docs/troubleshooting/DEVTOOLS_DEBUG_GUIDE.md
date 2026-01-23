# DevTools Debugging Guide - Question Extraction Issue

## Step-by-Step Instructions

### 1. Open Browser DevTools
- Press **F12** (or Cmd+Option+I on Mac)
- Click on the **Network** tab
- Make sure "Preserve log" is checked (checkbox at top of Network tab)

### 2. Prepare for Testing
- Clear the network log (click the 🚫 icon)
- Make sure you're on a project with context files uploaded
- Go to the **Questions** tab

### 3. Start Question Extraction
- Click "🤖 AI Prefill from Context" button
- Watch the network requests appear

### 4. Find the Prefill Request
Look for a request named:
```
prefill/{project-id}
```

It will be a **POST** request to `/api/questions/prefill/...`

### 5. Check the Request Details

Click on that request and check these tabs:

#### A. **Headers Tab**
- Status Code: Should be **200** (success) or **504** (timeout)
- Request Method: Should be **POST**
- Request URL: `/api/questions/prefill/{some-uuid}`

#### B. **Response Tab**
- Look for JSON response like:
```json
{
  "message": "AI prefilled X questions",
  "responses": [...]
}
```
- Count how many responses are in the array
- Check if there's an error message instead

#### C. **Timing Tab**
- Look at "Waiting for server response" time
- If it's > 60 seconds, we have a timeout issue
- If it's < 60 seconds but returns an error, we have a processing issue

### 6. Take Screenshots

Take screenshots of:
1. The Network tab with the prefill request highlighted
2. The Response tab showing the JSON (or error)
3. The Timing tab showing how long it took

---

## What We're Looking For

### ✅ Success Scenario
```
Status: 200 OK
Response: { "message": "AI prefilled 139 questions", "responses": [...] }
Timing: 120-180 seconds
```
**Means**: API is working! Progress bar just needs UI fix.

### ❌ Timeout Scenario
```
Status: 504 Gateway Timeout
Response: (empty or error)
Timing: ~60-120 seconds then timeout
```
**Means**: Vercel function timeout (need to upgrade plan or optimize)

### ⚠️ Partial Success Scenario
```
Status: 200 OK
Response: { "message": "AI prefilled 102 questions", "responses": [102 items] }
Timing: 90 seconds
```
**Means**: API is completing but not processing all questions

### ❌ Error Scenario
```
Status: 500 Internal Server Error
Response: { "error": "Some error message" }
Timing: Fast (<5 seconds)
```
**Means**: Backend error (likely AI API or database issue)

---

## While You're Checking...

Also check the **Console** tab for any JavaScript errors:
- Look for red error messages
- Check if there are any failed network requests
- Note any warnings about timeouts

---

## Quick Diagnostic Checklist

While watching the request:

- [ ] Does the request appear in Network tab?
- [ ] What is the status code? (200, 504, 500, other?)
- [ ] How long does it take? (seconds)
- [ ] Does it return a JSON response?
- [ ] If yes, how many `responses` are in the array?
- [ ] Does the progress counter ever update beyond 129?
- [ ] Any console errors?

---

## What to Share

Once you've checked, please share:

1. **Status Code**: (e.g., "200 OK" or "504 Timeout")
2. **Response Time**: How long the request took
3. **Response Data**:
   - If success: How many questions were prefilled?
   - If error: What's the error message?
4. **Progress Bar**: Did it ever move past 129?

This will tell us exactly what's failing and how to fix it!
