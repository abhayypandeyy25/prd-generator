# Authentication & Data Segregation Implementation

**Date**: January 24, 2026
**Status**: In Progress

---

## Overview

Implement user authentication and data segregation to ensure each user can only see their own projects and data.

---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────>│  Firebase    │─────>│  Supabase   │
│   (Vue.js)  │<─────│  Auth        │      │  (RLS)      │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                     │
       │              ID Token (JWT)         user_id filter
       │                     │                     │
       v                     v                     v
   AuthPage.vue      Verify Token          Row Level Security
   authStore.js      Middleware            user_id = auth.uid
```

---

## Implementation Steps

### Phase 1: Database Migration (Add user_id columns)

All tables need a `user_id` column to segregate data:
- `projects`
- `context_files`
- `features`
- `questions_responses`
- `prds`
- `prd_snapshots`
- `prd_templates` (optional - can be shared)
- `prd_comments`
- `share_links`
- `feedback`

### Phase 2: Row Level Security (RLS)

Enable RLS on all tables and add policies:
- Users can only SELECT/INSERT/UPDATE/DELETE their own data
- Share links have special read-only access
- Public templates are readable by all

### Phase 3: Backend API Authentication

Add middleware to:
1. Extract Firebase ID token from Authorization header
2. Verify token with Firebase Admin SDK
3. Add `user_id` to request context
4. Filter all queries by `user_id`

### Phase 4: Frontend Integration

1. Show AuthPage when not authenticated
2. Add ID token to all API requests
3. Handle token refresh
4. Add logout button
5. Protect routes

---

## Detailed Implementation

### 1. Database Migration

```sql
-- Add user_id to all tables
ALTER TABLE projects ADD COLUMN user_id VARCHAR(255);
ALTER TABLE context_files ADD COLUMN user_id VARCHAR(255);
ALTER TABLE features ADD COLUMN user_id VARCHAR(255);
ALTER TABLE questions_responses ADD COLUMN user_id VARCHAR(255);
ALTER TABLE prds ADD COLUMN user_id VARCHAR(255);
ALTER TABLE prd_snapshots ADD COLUMN user_id VARCHAR(255);
ALTER TABLE prd_comments ADD COLUMN user_id VARCHAR(255);
ALTER TABLE share_links ADD COLUMN user_id VARCHAR(255);
ALTER TABLE feedback ADD COLUMN user_id VARCHAR(255);

-- Create indexes for performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_context_files_user_id ON context_files(user_id);
CREATE INDEX idx_features_user_id ON features(user_id);
CREATE INDEX idx_questions_responses_user_id ON questions_responses(user_id);
CREATE INDEX idx_prds_user_id ON prds(user_id);
CREATE INDEX idx_prd_snapshots_user_id ON prd_snapshots(user_id);
CREATE INDEX idx_prd_comments_user_id ON prd_comments(user_id);
CREATE INDEX idx_share_links_user_id ON share_links(user_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
```

### 2. Row Level Security Policies

```sql
-- Enable RLS on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE features ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE prds ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Drop existing permissive policies (if any)
DROP POLICY IF EXISTS "Allow all on projects" ON projects;
DROP POLICY IF EXISTS "Allow all on context_files" ON context_files;
-- ... (drop all existing permissive policies)

-- Projects: Users can only access their own
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can insert own projects" ON projects
    FOR INSERT WITH CHECK (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (user_id = current_setting('app.user_id', true));

-- Context Files: Users can only access their own
CREATE POLICY "Users can view own context files" ON context_files
    FOR SELECT USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can insert own context files" ON context_files
    FOR INSERT WITH CHECK (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can delete own context files" ON context_files
    FOR DELETE USING (user_id = current_setting('app.user_id', true));

-- Features: Users can only access their own
CREATE POLICY "Users can view own features" ON features
    FOR SELECT USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can insert own features" ON features
    FOR INSERT WITH CHECK (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can update own features" ON features
    FOR UPDATE USING (user_id = current_setting('app.user_id', true));

CREATE POLICY "Users can delete own features" ON features
    FOR DELETE USING (user_id = current_setting('app.user_id', true));

-- ... (similar policies for other tables)

-- Special policy for shared PRDs
CREATE POLICY "Users can view shared PRDs" ON prds
    FOR SELECT USING (
        user_id = current_setting('app.user_id', true)
        OR id IN (
            SELECT prd_id FROM share_links
            WHERE is_active = true
            AND (expires_at IS NULL OR expires_at > NOW())
        )
    );
```

### 3. Backend Authentication Middleware

```python
# api/auth.py - Add Firebase Admin SDK verification

from firebase_admin import auth as firebase_admin_auth
import firebase_admin
from firebase_admin import credentials
import os

# Initialize Firebase Admin
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
    "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
})

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def verify_token(id_token):
    """
    Verify Firebase ID token and return user_id
    """
    try:
        decoded_token = firebase_admin_auth.verify_id_token(id_token)
        return decoded_token['uid']
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

def get_user_from_request(request):
    """
    Extract and verify user from Authorization header
    Returns user_id or None
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    id_token = auth_header.replace('Bearer ', '')
    return verify_token(id_token)

def require_auth(handler):
    """
    Decorator to require authentication for API endpoints
    """
    def wrapper(self):
        user_id = get_user_from_request(self)
        if not user_id:
            self.send_json(401, {'error': 'Unauthorized'})
            return

        # Set user_id in Supabase RLS context
        supabase.rpc('set_user_id', {'user_id': user_id}).execute()

        # Add user_id to handler
        self.user_id = user_id
        return handler(self)

    return wrapper
```

### 4. Update API Endpoints

All endpoints need to:
1. Use `@require_auth` decorator
2. Filter queries by `user_id`

Example:
```python
# api/projects.py

@require_auth
def do_GET(self):
    # self.user_id is now available
    result = supabase.from_('projects') \
        .select('*') \
        .eq('user_id', self.user_id) \
        .execute()
    ...

@require_auth
def do_POST(self):
    data = json.loads(self.rfile.read(content_length))
    data['user_id'] = self.user_id  # Add user_id to new projects

    result = supabase.from_('projects').insert(data).execute()
    ...
```

### 5. Frontend Changes

#### A. Update App.vue

```vue
<template>
  <AuthPage v-if="!authStore.isAuthenticated && !authStore.loading" />
  <div v-else-if="!authStore.loading" class="app">
    <!-- Existing app content -->
    <Header @logout="handleLogout" />
    <!-- ... -->
  </div>
  <div v-else class="loading-screen">
    <div class="spinner"></div>
    <p>Loading...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/authStore'
import AuthPage from './components/AuthPage.vue'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.initialize()
})

const handleLogout = async () => {
  await authStore.signOut()
}
</script>
```

#### B. Update API Service to Include Token

```javascript
// frontend/src/services/api.js

import { useAuthStore } from '../stores/authStore'

// Add request interceptor to include auth token
api.interceptors.request.use(async (config) => {
  const authStore = useAuthStore()
  const token = await authStore.getIdToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// Add response interceptor to handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.signOut()
    }
    return Promise.reject(error)
  }
)
```

#### C. Add Header Component with Logout

```vue
<!-- frontend/src/components/Header.vue -->
<template>
  <header class="app-header">
    <div class="header-content">
      <h1>PM Clarity</h1>
      <div class="header-right">
        <span class="user-email">{{ authStore.userEmail }}</span>
        <button @click="$emit('logout')" class="btn btn-logout">
          Logout
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

defineEmits(['logout'])
</script>
```

---

## Environment Variables

### Backend (Vercel)
```bash
# Firebase Admin SDK
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
```

### Frontend (.env.local)
```bash
# Firebase Client SDK (already exists)
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-app.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

---

## Testing Checklist

- [ ] User can sign up with email/password
- [ ] User can sign in with email/password
- [ ] User can sign in with Google
- [ ] User can logout
- [ ] Unauthenticated users see AuthPage
- [ ] Authenticated users see app
- [ ] API requests include auth token
- [ ] API rejects requests without valid token
- [ ] User can only see their own projects
- [ ] User can only see their own context files
- [ ] User can only see their own features
- [ ] User can only see their own PRDs
- [ ] Shared PRDs work correctly
- [ ] Token refresh works automatically
- [ ] Logout clears all data

---

## Migration Strategy

1. **Add user_id columns** (nullable initially)
2. **Run data migration** to set user_id for existing data
3. **Enable RLS** with policies
4. **Deploy backend auth** middleware
5. **Deploy frontend auth** integration
6. **Test thoroughly**
7. **Make user_id NOT NULL** after migration

---

## Security Considerations

1. **Token Verification**: Always verify Firebase ID tokens on backend
2. **RLS**: Double-layer security (API + Database)
3. **Token Refresh**: Implement automatic token refresh
4. **HTTPS**: Always use HTTPS in production
5. **Rate Limiting**: Add rate limiting to prevent abuse
6. **CORS**: Restrict CORS to your domain

---

## Rollback Plan

If issues arise:
1. **Remove RLS policies** (temporarily)
2. **Revert API changes** to allow all access
3. **Revert frontend** to remove auth requirement
4. **Keep user_id columns** for future retry

---

## Next Steps

1. Create migration file `migrations/005_authentication.sql`
2. Update all API endpoints with `@require_auth`
3. Integrate AuthPage in App.vue
4. Add Firebase Admin SDK to backend
5. Test locally
6. Deploy to production

