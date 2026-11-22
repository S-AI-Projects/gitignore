# R46-T010 Test Fixtures

## Template under test: `Global/Dreamweaver.gitignore`

Patterns tested: `_notes`, `_compareTemp`, `configs/`

Environment:
- Git: `git version 2.55.0`
- Python: `Python 3.14.7`

### Pattern mechanics

| Pattern | Matches | Purpose |
|---|---|---|
| `_notes` | Directories or files named `_notes` at any depth | Dreamweaver local site notes directory |
| `_compareTemp` | Directories or files named `_compareTemp` at any depth | Temporary comparison data |
| `configs/` | Directories named `configs` only (trailing slash) | Dreamweaver site configuration directory |

### Small project tree example

```
my-dreamweaver-project/
├── .gitignore           ← Global/Dreamweaver.gitignore
├── index.html           ← TRACKED (HTML source)
├── styles/
│   └── main.css         ← TRACKED (stylesheet)
├── scripts/
│   └── app.js           ← TRACKED (JavaScript)
├── images/
│   └── logo.png         ← TRACKED (image asset)
├── _notes/              ← IGNORED by _notes (line 6)
│   └── site-plan.txt    ← IGNORED (inside ignored _notes/)
├── _compareTemp/        ← IGNORED by _compareTemp (line 7)
│   └── index.html.tmp   ← IGNORED (inside ignored _compareTemp/)
└── configs/             ← IGNORED by configs/ (line 8)
    └── site.xml         ← IGNORED (inside ignored configs/)
```

---

## Suite 1 — Positive pattern checks (ignored outputs)

| # | Path | Type | Expected | Actual Result | Rule | Line |
|---|---|---|---|---|---|---|
| 1 | `_notes` | dir | IGNORED | IGNORED | `_notes` | 6 |
| 2 | `_notes/site-plan.txt` | file | IGNORED | IGNORED | `_notes` | 6 |
| 3 | `_compareTemp` | dir | IGNORED | IGNORED | `_compareTemp` | 7 |
| 4 | `_compareTemp/index.html.tmp` | file | IGNORED | IGNORED | `_compareTemp` | 7 |
| 5 | `configs` | dir | IGNORED | IGNORED | `configs/` | 8 |
| 6 | `configs/site.xml` | file | IGNORED | IGNORED | `configs/` | 8 |

---

## Suite 2 — configs/ trailing slash behavior

| # | Path | Type | Expected | Actual Result | Reason |
|---|---|---|---|---|---|
| 7 | `configs` | file | NOT IGNORED | NOT IGNORED | Trailing slash restricts to directories only |

---

## Suite 3 — Tracked inputs (should NOT be ignored)

| # | Path | Expected | Actual Result | Reason |
|---|---|---|---|---|
| 8 | `index.html` | NOT IGNORED | NOT IGNORED | HTML source file — primary web page |
| 9 | `styles/main.css` | NOT IGNORED | NOT IGNORED | Stylesheet |
| 10 | `scripts/app.js` | NOT IGNORED | NOT IGNORED | JavaScript |
| 11 | `images/logo.png` | NOT IGNORED | NOT IGNORED | Image asset |
| 12 | `README.md` | NOT IGNORED | NOT IGNORED | Documentation |

---

## Suite 4 — Near-miss names

| # | Path | Expected | Actual Result | Reason |
|---|---|---|---|---|
| 13 | `notes/` | NOT IGNORED | NOT IGNORED | No leading underscore |
| 14 | `_notes_backup/` | NOT IGNORED | NOT IGNORED | Extra suffix |
| 15 | `compareTemp/` | NOT IGNORED | NOT IGNORED | No leading underscore |

---

## Suite 5 — Tracked-file behaviour (`_notes`, `_compareTemp`, `configs/`)

Files matching each of the three patterns are committed *before* adding the `.gitignore` rule to demonstrate that ignore patterns do not untrack already-tracked files, validated via `git ls-files` and `git status --porcelain`:

| # | Action / Check | Command | Expected | Actual Result |
|---|---|---|---|---|
| 16 | Stage pre-gitignore matching files | `git add .` | returncode 0 | returncode 0 (staged) |
| 17 | Commit pre-gitignore matching files | `git commit -m ...` | returncode 0 | returncode 0 (committed) |
| 18 | Verify index: `_notes/site-notes.txt` | `git ls-files` | File in index | Verified in index |
| 19 | Verify index: `_compareTemp/compare.tmp` | `git ls-files` | File in index | Verified in index |
| 20 | Verify index: `configs/site.xml` | `git ls-files` | File in index | Verified in index |
| 21 | Clean porcelain status | `git status --porcelain` | Tracked files clean | Verified clean (`'?? .gitignore'`) |
| 22 | Modify tracked `_notes/site-notes.txt` | `git status --porcelain` | Shows ` M _notes/site-notes.txt` | Verified detected (`' M _notes/site-notes.txt'`) |
| 23 | Modify tracked `_compareTemp/compare.tmp` | `git status --porcelain` | Shows ` M _compareTemp/compare.tmp` | Verified detected (`' M _compareTemp/compare.tmp'`) |
| 24 | Modify tracked `configs/site.xml` | `git status --porcelain` | Shows ` M configs/site.xml` | Verified detected (`' M configs/site.xml'`) |
| 25 | Index check-ignore | `git check-ignore -v <path>` | returncode 1 (not ignored) | Verified not ignored in index mode |
| 26 | Untracked file comparison | `git status --porcelain <new_file>` | Output empty (ignored) | Output empty (`""`) |

---

## Summary of Results

Total checks: **26/26 PASSED**
- Suite 1 (Positive pattern checks): 6 checks passed
- Suite 2 (configs/ trailing slash): 1 check passed
- Suite 3 (Tracked inputs): 5 checks passed
- Suite 4 (Near-miss patterns): 3 checks passed
- Suite 5 (Tracked-file behaviour): 11 checks passed
