
# R46-T008 Test Fixtures

## Template under test: `CodeIgniter.gitignore`

Patterns tested: `*/config/development`, `*/logs/log-*.php`, `!*/logs/index.html`

### Pattern mechanics

| Pattern | Description |
|---|---|
| `*/config/development` | Ignores the development-only configuration directory at any depth |
| `*/logs/log-*.php` | Ignores date-stamped CodeIgniter log files in any `logs/` directory |
| `!*/logs/index.html` | Negation: re-includes `index.html` so the logs directory listing gate is tracked |

### Negation last-match behavior

gitignore processes rules top-to-bottom; the last matching rule wins. When
`!*/logs/index.html` appears after `*/logs/log-*.php`, it overrides the earlier
ignore for paths named `index.html` inside `*/logs/`. As a result, `index.html`
is NOT ignored even though it is inside an otherwise-ignored directory.

**Important**: `git check-ignore -v --no-index` returns exit code 0 for paths
matched by a negation rule, but the file is NOT effectively ignored. Use
`git status --porcelain` for authoritative check (output `??` = not ignored).

---

## Suite 1 — Positive pattern checks

| # | Path | Type | Expected | Responsible rule |
|---|---|---|---|---|
| 1 | `application/config/development` | dir | IGNORED | `.gitignore:1:*/config/development` |
| 2 | `myapp/logs/log-2024-01-15.php` | file | IGNORED | `.gitignore:2:*/logs/log-*.php` |
| 3 | `myapp/logs/log-2024-12-01.php` | file | IGNORED | `.gitignore:2:*/logs/log-*.php` |
| 4 | `application/logs/error.log` | file | IGNORED | `.gitignore:15:application/logs/*` |
| 5 | `application/logs/log-2024-01-15.php` | file | IGNORED | `.gitignore:15:application/logs/*` (last match) |

---

## Suite 2 — Negation rule checks

| # | Path | Expected | Rule controlling |
|---|---|---|---|
| 6 | `myapp/logs/index.html` | NOT IGNORED | `!*/logs/index.html` negation |
| 7 | `application/logs/index.html` | NOT IGNORED | `!application/logs/index.html` negation |
| 8 | `application/logs/other.html` | IGNORED | `application/logs/*` |

---

## Suite 3 — Negative (near-miss) pattern checks

| # | Path | Expected | Reason |
|---|---|---|---|
| 9 | `application/config/production/database.php` | NOT IGNORED | Only `development` dir is ignored |
| 10 | `application/logs/app.log` | IGNORED | `application/logs/*` CI3 rule |
| 11 | `application/controllers/Welcome.php` | NOT IGNORED | Source file |
| 12 | `README.md` | NOT IGNORED | Documentation |

---

## Notes

- Last-match ordering: `application/logs/*` (line 15) is later than `*/logs/log-*.php` (line 2).
  For `application/logs/log-*.php`, git reports line 15 as the responsible rule.
- `git check-ignore --no-index` reports exit 0 for negation rules; `git status` is authoritative.
- All tests use temporary Git repositories; the shared project checkout is never modified.
