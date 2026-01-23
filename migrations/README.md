# Database Migrations

## How to Run Migrations

### Prerequisites
- Access to Supabase dashboard
- SQL Editor access

### Steps
1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql/new
2. Copy the SQL from each migration file
3. Execute in order (001 → 002 → 003 → 004)
4. Verify each migration completed successfully

---

## Migration Files

### 001_prd_editing.sql
**PRD Editing & Version History**
- `generated_prds` table
- `prd_edit_snapshots` table for version history
- PRD editing and rollback functionality

**Status**: ✅ Applied

---

### 002_templates.sql
**Templates & Customization System**
- `prd_templates` table (5 default templates)
- `template_sections` table
- `custom_questions` table
- Template selection and customization

**Status**: ✅ Applied

**Templates Included**:
1. Lean PRD (Startup) - Default
2. Detailed PRD (Enterprise)
3. Technical Spec (Engineering)
4. One-Pager (Executive)
5. Feature Brief

---

### 003_collaboration.sql
**Collaboration & Sharing**
- `share_links` table
- `comments` table with threading support
- PRD sharing with optional passwords
- Commenting system

**Status**: ✅ Applied

---

### 004_feedback.sql
**AI Improvement Loop**
- `prd_feedback` table
- `question_feedback` table
- Rating and feedback collection
- AI-driven improvements based on feedback

**Status**: ✅ Applied

---

## Migration Status

| # | Migration | Tables Created | Status |
|---|-----------|----------------|--------|
| 001 | PRD Editing | 2 tables | ✅ |
| 002 | Templates | 3 tables | ✅ |
| 003 | Collaboration | 2 tables | ✅ |
| 004 | Feedback | 2 tables | ✅ |

**Total Tables**: 9 additional tables

---

## Verification Queries

### Check if all tables exist
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'generated_prds',
  'prd_edit_snapshots',
  'prd_templates',
  'template_sections',
  'custom_questions',
  'share_links',
  'comments',
  'prd_feedback',
  'question_feedback'
)
ORDER BY table_name;
```

Should return 9 rows.

### Check template data
```sql
SELECT name, is_default, section_count
FROM prd_templates
LEFT JOIN (
  SELECT template_id, COUNT(*) as section_count
  FROM template_sections
  GROUP BY template_id
) AS counts ON prd_templates.id = counts.template_id
ORDER BY is_default DESC, name;
```

Should return 5 templates.

---

## Rollback (If Needed)

To rollback a migration:

```sql
-- Example: Remove templates migration
DROP TABLE IF EXISTS custom_questions CASCADE;
DROP TABLE IF EXISTS template_sections CASCADE;
DROP TABLE IF EXISTS prd_templates CASCADE;
ALTER TABLE projects DROP COLUMN IF EXISTS template_id;
```

**⚠️ Warning**: This will delete all data in these tables!

---

## Detailed Migration Guide

For step-by-step instructions with screenshots:
- See [../docs/deployment/MIGRATION_TEMPLATES.md](../docs/deployment/MIGRATION_TEMPLATES.md)

---

## Troubleshooting

### Migration fails with "permission denied"
- Ensure you're using the service_role key, not anon key
- Check RLS policies are set correctly

### Tables not showing up
- Refresh the Supabase dashboard
- Check the schema is 'public'
- Verify the migration SQL executed without errors

### Duplicate key errors
- Migration was already run
- Check if tables exist: `SELECT * FROM information_schema.tables WHERE table_name = 'prd_templates';`
