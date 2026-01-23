# PM Clarity Test Suite

## Overview

Comprehensive test suite with 115 tests covering core features, advanced features, and integrations.

---

## Running Tests

### Automated API Tests

```bash
cd tests
chmod +x run_evals.sh
./run_evals.sh
```

This will:
- Test all API endpoints
- Verify CRUD operations
- Check advanced features
- Generate test report

### Manual UI Tests

See [EVALS.md](./EVALS.md) sections:
- Frontend UI Tests
- User Guidance Tests
- Edge Cases

---

## Test Coverage

| Category | Tests | Critical |
|----------|-------|----------|
| **Core Features** |
| API Health | 2 | 2 |
| Projects | 5 | 5 |
| Context Files | 6 | 5 |
| Features | 7 | 6 |
| Questions | 8 | 7 |
| PRD Generation | 5 | 5 |
| **Advanced Features** |
| PRD Editing | 5 | 4 |
| Templates | 5 | 3 |
| Collaboration | 8 | 5 |
| Version History | 3 | 2 |
| Smart Context Analysis | 6 | 4 |
| Adaptive Questioning | 6 | 4 |
| Stakeholder Views | 5 | 3 |
| AI Improvement Loop | 6 | 4 |
| Analytics | 6 | 3 |
| **Quality & Integration** |
| Frontend UI | 8 | 6 |
| Data Consistency | 8 | 6 |
| User Guidance | 6 | 4 |
| Edge Cases | 5 | 3 |
| Integration Tests | 5 | 2 |
| **Total** | **115** | **83** |

---

## Test Categories

### 1. API Health Checks (2 tests)
Basic API connectivity and health endpoint

### 2. Core CRUD Operations (31 tests)
- Projects: Create, list, get, delete
- Context: Upload, list, delete, extract text
- Features: Extract, list, toggle, CRUD
- Questions: List, prefill, save, confirm
- PRD: Generate, retrieve, export

### 3. Advanced Features (50 tests)
- PRD Editing & Refinement
- Templates & Customization
- Collaboration & Sharing
- Version History & Comparison
- Smart Context Analysis
- Adaptive Questioning
- Stakeholder Views
- AI Improvement Loop
- Analytics & Insights

### 4. Integration & Quality (32 tests)
- Frontend UI flows
- Data consistency across features
- User guidance and error handling
- Edge case handling
- Full workflow integration

---

## Test Environment

### Required Setup

1. **API Running**:
   ```bash
   # Production
   https://pm-clarity.vercel.app/api

   # Local
   cd frontend && npm run dev
   ```

2. **Environment Variables**:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ANTHROPIC_API_KEY`

3. **Database Migrations**:
   All migrations (001-004) must be applied

---

## Test Data

### Sample Project Setup
```bash
# Create test project
PROJECT_ID=$(curl -X POST https://pm-clarity.vercel.app/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project"}' | jq -r '.id')

# Upload context
curl -X POST https://pm-clarity.vercel.app/api/context/upload/$PROJECT_ID \
  -F "files=@test_data/sample.txt"

# Extract features
curl -X POST https://pm-clarity.vercel.app/api/features/extract/$PROJECT_ID
```

See [EVALS.md](./EVALS.md) for complete test data templates.

---

## Continuous Integration

### GitHub Actions (Optional)

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: cd tests && ./run_evals.sh
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Test Results

### Expected Pass Rate
- **Critical Tests**: 100% (83/83)
- **All Tests**: ≥95% (110+/115)

### Common Failures
1. **AI API Rate Limits**: Retry with backoff
2. **Timeout on Large Context**: Increase batch size limits
3. **Flaky Network**: Retry failed requests

---

## Adding New Tests

### 1. Update EVALS.md
Add test case with:
- Test ID
- Description
- Steps
- Expected result
- Priority (Critical/Standard)

### 2. Update run_evals.sh
Add API test:
```bash
echo "Testing new feature..."
test_api "POST" "/api/new-feature" '{"data":"test"}'
```

### 3. Update Test Count
Update the total count in README.md and EVALS.md

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All migrations applied
- [ ] API health check passes
- [ ] Core CRUD operations work
- [ ] Advanced features functional
- [ ] No critical test failures
- [ ] Manual UI smoke test completed

See [EVALS.md](./EVALS.md) for full pre-deployment checklist.

---

## Documentation

- **Full Test Suite**: [EVALS.md](./EVALS.md)
- **Test Runner**: [run_evals.sh](./run_evals.sh)
- **Bug Reports**: [../docs/troubleshooting/](../docs/troubleshooting/)
