# R46-T030 — CFWheels.gitignore

**Task ID**: R46-T030 | **Issue**: #30 | **Student**: E26B07F0687

## Realistic Project Tree

```
myapp/
  controllers/Account.cfc        ← tracked source
  models/User.cfc                ← tracked source
  views/account/index.cfm        ← tracked source
  config/settings.cfm            ← tracked source
  plugins/DBMigrate/index.cfm   ← IGNORED (plugins/**/*) — binary plugin
  plugins/Wheels/assets/logo.png ← IGNORED (plugins/**/*) — deep plugin asset
  files/images/avatar.jpg        ← IGNORED (files) — user upload
  db/sql/001_create_users.sql    ← IGNORED (db/sql) — generated migration
  db/seeds.cfm                   ← TRACKED  — hand-written seed
  javascripts/bundles/app.min.js ← IGNORED (javascripts/bundles) — generated
  stylesheets/bundles/main.min.css ← IGNORED (stylesheets/bundles) — generated
  javascripts/app.js             ← TRACKED  — source JS
```

## Focus Patterns

| Pattern | Purpose |
|---------|---------|
| `plugins/**/*` | Ignore all files inside plugins/ at any depth; dir itself stays visible |
| `files` | Ignore the runtime upload directory (file or dir named 'files') |
| `db/sql` | Ignore auto-generated SQL migrations; hand-written db scripts tracked |

## Pattern Analysis

### `plugins/**/*` vs Alternatives
- `plugins/` → entire directory hidden, losing folder structure in git tree
- `plugins/*` → only one level deep; misses `plugins/Wheels/assets/logo.png`
- `plugins/**/*` → ignores **all file content** while keeping folder scaffolding visible ✓

### `files` vs Alternatives
- `files/` → only matches if 'files' is a directory; misses edge cases
- `files` → matches both a file and a directory named 'files' ✓

### `db/sql` vs Alternatives
- `db/` → too broad; hides hand-written `db/seeds.cfm`
- `db/sql/*.sql` → misses files without `.sql` extension
- `db/sql` → ignores the entire sub-tree under `db/sql/` ✓

## Results
| Check | Count |
|-------|-------|
| Total | 16 |
| Passed | 15 |
| Failed | 1 |

See `evidence.json` for full structured evidence.
