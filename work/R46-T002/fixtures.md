
# R46-T002 Test Fixtures

Fixtures are created in a fresh temporary Git repository outside the shared
project checkout during each run of `check.py`.

## .gitignore under test

The test uses the actual template file:

`Global/EiffelStudio.gitignore`

The test copies this file into a fresh temporary Git repository.
It does not create a separate synthetic `.gitignore` file.

Rule verified:
- Line: 7
- Pattern: `EIFGENs`
- Pattern type: Bare directory-name pattern (no slashes)
- Expected behaviour: Matches directories named `EIFGENs` at any depth.

---

## Fixtures

| # | Path | Type | Expected | Reason |
|---|---|---|---|---|
| 1 | `EIFGENs/` | dir | IGNORED | Exact name match at root depth |
| 2 | `EIFGENs/W_code` | file | IGNORED | Inside an ignored directory |
| 3 | `project/EIFGENs/` | dir | IGNORED | Bare-name pattern matches at one level deep |
| 4 | `project/EIFGENs/W_code` | file | IGNORED | Inside an ignored directory one level deep |
| 5 | `deep/nested/EIFGENs/` | dir | IGNORED | Bare-name pattern matches at two levels deep |
| 6 | `deep/nested/EIFGENs/W_code` | file | IGNORED | Inside an ignored directory two levels deep |
| 7 | `EIFGENs-backup/` | dir | NOT IGNORED | Different directory name |
| 8 | `EIFGENs-backup/notes.txt` | file | NOT IGNORED | Parent is not ignored |
| 9 | `EIFGENs_extra/` | dir | NOT IGNORED | Different directory name |
| 10 | `EIFGENs_extra/notes.txt` | file | NOT IGNORED | Parent is not ignored |
| 11 | `EIGENS/` | dir | NOT IGNORED | Misspelling |
| 12 | `EIGENS/notes.txt` | file | NOT IGNORED | Parent is not ignored |
| 13 | `main.e` | file | NOT IGNORED | Legitimate Eiffel source file |
| 14 | `config.ecf` | file | NOT IGNORED | Legitimate Eiffel configuration file |
| 15 | `README.md` | file | NOT IGNORED | Documentation file |

---

## Tracked-file fixture

| Path | Action | Expected behaviour |
|---|---|---|
| `project/EIFGENs/tracked.e` | Force-added and committed | File is present in the Git index |
| `project/EIFGENs/tracked.e` | `git check-ignore -v` | Not reported as ignored because it is tracked |
| `project/EIFGENs/tracked.e` | `git check-ignore -v --no-index` | Pattern is reported as matching |
| `project/EIFGENs/tracked.e` | `git status --porcelain` | No changes; tracked file is clean |

---

## Notes on macOS case-insensitive filesystem

macOS commonly uses a case-insensitive, case-preserving filesystem by default.
Creating a directory named `eifgens` alongside `EIFGENs` may cause them to
refer to the same directory.

For this reason, the fixture set does not include a separate lowercase
`eifgens` test. It cannot be reliably tested on a case-insensitive filesystem.
