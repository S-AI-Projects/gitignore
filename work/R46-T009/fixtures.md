
# R46-T009 Test Fixtures

## Template under test: `Global/Otto.gitignore`

Pattern tested: `.otto/`

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

| # | Path | Type | Expected | Result |
|---|---|---|---|---|
| 1 | `.otto` | directory | IGNORED | `.gitignore:1:.otto/` |
| 2 | `.otto/compiled.json` | file inside dir | IGNORED | `.gitignore:1:.otto/` |
| 3 | `.otto` | file | NOT IGNORED | Trailing slash restricts to dirs |

---

## Suite 2 — Broader alternative: `.otto` (without trailing slash)

| # | Path | Type | Expected by real rule | Result with broader |
|---|---|---|---|---|
| 4 | `.otto` | directory | IGNORED | IGNORED (correct) |
| 5 | `.otto` | file | NOT IGNORED | IGNORED ← **FALSE POSITIVE** |

---

## Suite 3 — Narrower alternative: `/.otto/` (anchored to root)

| # | Path | Type | Expected by real rule | Result with narrower |
|---|---|---|---|---|
| 6 | `.otto` (root) | directory | IGNORED | IGNORED (correct) |
| 7 | `subproject/.otto` | nested directory | IGNORED | NOT IGNORED ← **FALSE NEGATIVE** |

---

## Suite 4 — Near-miss names (original `.otto/` rule)

| # | Path | Expected |
|---|---|---|
| 8 | `.otto_backup/` | NOT IGNORED |
| 9 | `otto/` | NOT IGNORED |
| 10 | `README.md` | NOT IGNORED |
