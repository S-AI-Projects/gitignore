
# R46-T010 Test Fixtures

## Template under test: `Global/Dreamweaver.gitignore`

Patterns tested: `_notes`, `_compareTemp`, `configs/`

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
├── _notes/              ← IGNORED by _notes (line 2)
│   └── site-plan.txt    ← IGNORED (inside ignored _notes/)
├── _compareTemp/        ← IGNORED by _compareTemp (line 3)
│   └── index.html.tmp   ← IGNORED (inside ignored _compareTemp/)
└── configs/             ← IGNORED by configs/ (line 4)
    └── site.xml         ← IGNORED (inside ignored configs/)
```

---

## Suite 1 — Positive pattern checks (ignored outputs)

| # | Path | Type | Rule | Line |
|---|---|---|---|---|
| 1 | `_notes` | dir | `_notes` | 2 |
| 2 | `_notes/site-plan.txt` | file | `_notes` | 2 |
| 3 | `_compareTemp` | dir | `_compareTemp` | 3 |
| 4 | `_compareTemp/index.html.tmp` | file | `_compareTemp` | 3 |
| 5 | `configs` | dir | `configs/` | 4 |
| 6 | `configs/site.xml` | file | `configs/` | 4 |

---

## Suite 2 — configs/ trailing slash behavior

| # | Path | Type | Expected | Reason |
|---|---|---|---|---|
| 7 | `configs` | file | NOT IGNORED | Trailing slash restricts to directories only |

---

## Suite 3 — Tracked inputs (should NOT be ignored)

| # | Path | Expected | Rule that matched |
|---|---|---|---|
| 8 | `index.html` | NOT IGNORED | — (HTML source) |
| 9 | `styles/main.css` | NOT IGNORED | — (stylesheet) |
| 10 | `scripts/app.js` | NOT IGNORED | — (JavaScript) |
| 11 | `images/logo.png` | NOT IGNORED | — (image) |
| 12 | `README.md` | NOT IGNORED | — (documentation) |

---

## Suite 4 — Near-miss names

| # | Path | Expected | Reason |
|---|---|---|---|
| 13 | `notes/` | NOT IGNORED | No leading underscore |
| 14 | `_notes_backup/` | NOT IGNORED | Extra suffix |
| 15 | `compareTemp/` | NOT IGNORED | No leading underscore |
