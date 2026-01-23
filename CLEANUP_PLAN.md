# PM Clarity - Folder Structure Cleanup Plan

## Current Issues

1. **Too many markdown files in root** (8 files cluttering the root)
2. **Unused backend/ folder** (Flask/Railway setup not in use)
3. **Duplicate migration files** (002_templates.sql exists twice)
4. **Mixed documentation types** (dev logs, guides, evals all in root)

---

## Proposed Clean Structure

```
pm-clarity/
├── README.md                    # Main project overview (KEEP)
├── .env.example                 # Environment template (KEEP)
├── .gitignore                   # Git ignore rules (KEEP)
├── vercel.json                  # Deployment config (KEEP)
├── requirements.txt             # Python dependencies (KEEP)
├── supabase_schema.sql         # Initial DB schema (KEEP)
│
├── api/                         # Serverless functions (KEEP)
│   ├── *.py                     # All API handlers
│   └── data/                    # Static data files
│
├── frontend/                    # Vue.js app (KEEP)
│   ├── src/
│   ├── public/
│   └── package.json
│
├── docs/                        # NEW: All documentation
│   ├── README.md                # Docs index
│   ├── DEVELOPMENT_LOG.md       # Dev history
│   ├── FEATURE_ROADMAP.md       # Future features
│   ├── deployment/              # NEW: Deployment guides
│   │   ├── MIGRATION_TEMPLATES.md
│   │   └── VERCEL_SETUP.md
│   └── troubleshooting/         # NEW: Debug guides
│       ├── BUGFIX_JAN23.md
│       ├── CURRENT_STATUS.md
│       └── DEVTOOLS_DEBUG_GUIDE.md
│
├── migrations/                  # Database migrations (KEEP)
│   ├── README.md                # NEW: Migration guide
│   ├── 001_prd_editing.sql
│   ├── 002_templates.sql        # Keep one version
│   ├── 003_collaboration.sql
│   └── 004_feedback.sql
│
└── tests/                       # NEW: Testing files
    ├── EVALS.md                 # Test cases
    └── run_evals.sh             # Test runner

REMOVED:
- backend/                       # Flask setup (not used with Vercel)
- Dockerfile                     # Docker setup (not used)
- railway.json                   # Railway config (not used)
- migrations/002_templates_READY_TO_RUN.sql  # Duplicate
```

---

## Step-by-Step Cleanup Actions

### Phase 1: Create New Folders
```bash
mkdir -p docs/deployment
mkdir -p docs/troubleshooting
mkdir -p tests
```

### Phase 2: Move Documentation Files
```bash
# Move dev documentation
mv DEVELOPMENT_LOG.md docs/
mv FEATURE_ROADMAP.md docs/

# Move deployment guides
mv MIGRATION_TEMPLATES.md docs/deployment/
# Create deployment index later

# Move troubleshooting guides
mv BUGFIX_JAN23.md docs/troubleshooting/
mv CURRENT_STATUS.md docs/troubleshooting/
mv DEVTOOLS_DEBUG_GUIDE.md docs/troubleshooting/
```

### Phase 3: Move Test Files
```bash
mv EVALS.md tests/
mv run_evals.sh tests/
```

### Phase 4: Remove Unused Files
```bash
# Remove unused backend setup
rm -rf backend/

# Remove unused deployment configs
rm Dockerfile
rm railway.json

# Remove duplicate migration
rm migrations/002_templates_READY_TO_RUN.sql
```

### Phase 5: Create Index Files

**docs/README.md**:
```markdown
# PM Clarity Documentation

## Getting Started
- [Main README](../README.md) - Project overview
- [Development Log](./DEVELOPMENT_LOG.md) - Development history

## Deployment
- [Database Migration Guide](./deployment/MIGRATION_TEMPLATES.md)
- [Vercel Setup](./deployment/VERCEL_SETUP.md)

## Troubleshooting
- [Current Status](./troubleshooting/CURRENT_STATUS.md)
- [Bug Fixes Log](./troubleshooting/BUGFIX_JAN23.md)
- [DevTools Debug Guide](./troubleshooting/DEVTOOLS_DEBUG_GUIDE.md)

## Features
- [Feature Roadmap](./FEATURE_ROADMAP.md)

## Testing
- [Evaluation Suite](../tests/EVALS.md)
```

**migrations/README.md**:
```markdown
# Database Migrations

## Running Migrations

1. Open Supabase SQL Editor
2. Run migrations in order:
   - 001_prd_editing.sql
   - 002_templates.sql
   - 003_collaboration.sql
   - 004_feedback.sql

## Migration Status

| Migration | Description | Status |
|-----------|-------------|--------|
| 001 | PRD Editing & Versioning | ✅ |
| 002 | Templates System | ✅ |
| 003 | Collaboration & Sharing | ✅ |
| 004 | Feedback & AI Loop | ✅ |

See [docs/deployment/MIGRATION_TEMPLATES.md](../docs/deployment/MIGRATION_TEMPLATES.md) for detailed instructions.
```

**tests/README.md**:
```markdown
# PM Clarity Test Suite

## Running Tests

```bash
cd tests
./run_evals.sh
```

## Test Coverage

See [EVALS.md](./EVALS.md) for full test suite (115 tests).

## Test Categories
- API Health Checks
- CRUD Operations
- Advanced Features
- Integration Tests
- UI Tests
```

---

## Final Clean Structure Benefits

### ✅ Improved Organization
- All docs in one place (`docs/`)
- Tests separated (`tests/`)
- Deployment guides grouped (`docs/deployment/`)
- Troubleshooting isolated (`docs/troubleshooting/`)

### ✅ Cleaner Root
- Only 6 essential files in root
- No markdown clutter
- Clear separation of concerns

### ✅ Better Navigation
- Index files in each folder
- Related files grouped together
- Easier to find documentation

### ✅ Removed Dead Code
- No unused backend/ folder
- No Docker/Railway configs
- No duplicate files

---

## Git Operations (Optional)

If you want to preserve git history:
```bash
# Use git mv instead of mv
git mv DEVELOPMENT_LOG.md docs/
git mv BUGFIX_JAN23.md docs/troubleshooting/
# ... etc

# Remove with git
git rm -rf backend/
git rm Dockerfile railway.json
```

Otherwise, regular mv/rm is fine and simpler.

---

## Execution Order

1. ✅ Create new folders
2. ✅ Move documentation files
3. ✅ Move test files
4. ✅ Create index files
5. ✅ Remove unused files
6. ✅ Update README.md links
7. ✅ Commit changes

---

## Before You Start

**Backup first!**
```bash
cd ..
cp -r pm-clarity pm-clarity-backup
```

Or just commit current state:
```bash
git add .
git commit -m "Checkpoint before folder restructure"
```
