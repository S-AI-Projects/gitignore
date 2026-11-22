# R46-T009 Test Fixtures

## Template under test: `Global/Otto.gitignore`

Pattern tested: `.otto/` (line 7)

Environment:
- Git: `git version 2.55.0`
- Python: `Python 3.14.7`

### Pattern mechanics

| Pattern | Matches | Does NOT match |
|---|---|---|
| `.otto/` | Directories named `.otto` at any depth | Regular files named `.otto` |
| `.otto` (broader) | Both directories AND files named `.otto` | — |
| `/.otto/` (narrower) | Only the root-level `.otto/` directory | Nested `.otto/` directories |

### Why .otto/ is correct

- **Trailing slash** (`/`) restricts the pattern to directories only. Files named `.otto`
  are intentionally not ignored.
- **No leading slash** means the pattern matches at any depth (root or nested).
- The narrower `/.otto/` would miss `.otto/` directories inside subdirectories (false negative).
- The broader `.otto` without trailing slash would also ignore a file named `.otto` (false positive).

---

## Suite 1 — Original rule behavior: `.otto/`

| # | Path | Type | Expected | Actual Result | Rule Matched |
|---|---|---|---|---|---|
| 1 | `.otto` | directory | IGNORED | IGNORED | `.gitignore:7:.otto/` |
| 2 | `.otto/compiled.json` | file inside dir | IGNORED | IGNORED | `.gitignore:7:.otto/` |
| 3 | `.otto` | file | NOT IGNORED | NOT IGNORED | None (exit 1 — trailing slash restricts to dirs) |

---

## Suite 2 — Broader alternative: `.otto` (without trailing slash)

| # | Path | Type | Expected by real rule | Actual Result with broader | Evaluation |
|---|---|---|---|---|---|
| 4 | `.otto` | directory | IGNORED | IGNORED | Correct |
| 5 | `.otto` | file | NOT IGNORED | IGNORED | **FALSE POSITIVE** (broader rule incorrectly ignores files) |

---

## Suite 3 — Narrower alternative: `/.otto/` (anchored to root)

| # | Path | Type | Expected by real rule | Actual Result with narrower | Evaluation |
|---|---|---|---|---|---|
| 6 | `.otto` (root) | directory | IGNORED | IGNORED | Correct |
| 7 | `subproject/.otto` | nested directory | IGNORED | NOT IGNORED | **FALSE NEGATIVE** (anchored rule misses nested dirs) |

---

## Suite 4 — Near-miss names (original `.otto/` rule)

| # | Path | Expected | Actual Result | Reason |
|---|---|---|---|---|
| 8 | `.otto_backup/` | NOT IGNORED | NOT IGNORED | Different folder name (suffix appended) |
| 9 | `otto/` | NOT IGNORED | NOT IGNORED | No leading dot |
| 10 | `README.md` | NOT IGNORED | NOT IGNORED | Unrelated source/doc file |

---

## Suite 5 — Tracked-file behaviour (`.otto/tracked.txt`)

Demonstrates that an already-tracked file committed before adding `.gitignore` is not hidden or removed from Git status merely because it matches `.otto/`:

| # | Action / Check | Tool / Command | Expected | Actual Result |
|---|---|---|---|---|
| 11 | Stage pre-gitignore file | `git add .otto/tracked.txt` | returncode 0 | returncode 0 (staged) |
| 12 | Commit pre-gitignore file | `git commit -m ...` | returncode 0 | returncode 0 (committed) |
| 13 | Verify clean status | `git status --porcelain` | `.otto/tracked.txt` not untracked/ignored | Verified clean (`'?? .gitignore'`) |
| 14 | Verify index presence | `git ls-files .otto/tracked.txt` | File listed in index | Verified (`.otto/tracked.txt`) |
| 15 | Modify tracked file | `git status --porcelain .otto/tracked.txt` | Shows ` M .otto/tracked.txt` | Verified (`' M .otto/tracked.txt'`) |
| 16 | Index check-ignore | `git check-ignore -v .otto/tracked.txt` | returncode 1 (not ignored) | returncode 1 (not reported as ignored) |
| 17 | No-index check-ignore | `git check-ignore -v --no-index .otto/tracked.txt` | Matches `.otto/` pattern | Rule: `.gitignore:7:.otto/` |
| 18 | Untracked file comparison | `git status --porcelain .otto/untracked.txt` | Output empty (actively ignored) | Output empty (`""`) |

---

## Summary of Results

Total checks: **18/18 PASSED**
- Suite 1 (Original rule): 3 checks passed
- Suite 2 (Broader false positive): 2 checks passed
- Suite 3 (Narrower false negative): 2 checks passed
- Suite 4 (Near-misses): 3 checks passed
- Suite 5 (Tracked-file behaviour): 8 checks passed
