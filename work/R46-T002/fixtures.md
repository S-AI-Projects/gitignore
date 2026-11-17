# R46-T002 Test Fixtures

Fixtures were created in a fresh temporary Git repository (outside the shared
project checkout) during each run of `check.py`.  The table below documents
each fixture, its purpose, and the expected outcome.

## .gitignore under test

```
# The compilation directory
EIFGENs
```

Line 1 — comment.  
Line 2 — the rule under test: `EIFGENs` (bare name, no slashes).

---

## Fixtures

| # | Path                              | Type  | Expected    | Reason                                              |
|---|-----------------------------------|-------|-------------|-----------------------------------------------------|
| 1 | `EIFGENs/`                        | dir   | IGNORED     | Exact name match at root depth                      |
| 2 | `EIFGENs/W_code`                  | file  | IGNORED     | Inside an ignored directory                         |
| 3 | `project/EIFGENs/`                | dir   | IGNORED     | Bare-name pattern matches at any depth (1 level)    |
| 4 | `project/EIFGENs/W_code`          | file  | IGNORED     | Inside an ignored directory one level deep          |
| 5 | `deep/nested/EIFGENs/`            | dir   | IGNORED     | Bare-name pattern matches at any depth (2 levels)   |
| 6 | `deep/nested/EIFGENs/W_code`      | file  | IGNORED     | Inside an ignored directory two levels deep         |
| 7 | `EIFGENs-backup/`                 | dir   | NOT IGNORED | Suffix "-backup" makes it a different name          |
| 8 | `EIFGENs-backup/notes.txt`        | file  | NOT IGNORED | Parent is not ignored                               |
| 9 | `EIFGENs_extra/`                  | dir   | NOT IGNORED | Suffix "_extra" makes it a different name           |
|10 | `EIFGENs_extra/notes.txt`         | file  | NOT IGNORED | Parent is not ignored                               |
|11 | `EIGENS/`                         | dir   | NOT IGNORED | Misspelling — "F" is missing                        |
|12 | `EIGENS/notes.txt`                | file  | NOT IGNORED | Parent is not ignored                               |
|13 | `main.e`                          | file  | NOT IGNORED | Legitimate Eiffel source file                       |
|14 | `config.ecf`                      | file  | NOT IGNORED | Legitimate Eiffel configuration file                |
|15 | `README.md`                       | file  | NOT IGNORED | Documentation — always unignored                   |

## Tracked-file fixture

| Path                              | Action                      | Expected behaviour                                  |
|-----------------------------------|-----------------------------|-----------------------------------------------------|
| `project/EIFGENs/tracked.e`       | `git add -f` then committed | Tracked; `git check-ignore -v` (with index) exits 1 |
|                                   |                             | `git check-ignore -v --no-index` exits 0 (pattern still matches without index) |

## Notes on macOS case-insensitive filesystem

macOS uses a case-insensitive (but case-preserving) HFS+ / APFS filesystem by
default.  Creating a directory `eifgens` after `EIFGENs` already exists causes
them to merge.  For this reason the fixture set does not include a separate
`eifgens` case-insensitivity test — it cannot be reliably created on macOS.
On a case-sensitive Linux filesystem, `eifgens` would remain unignored because
gitignore patterns are matched with the same case-sensitivity as the
underlying filesystem.
