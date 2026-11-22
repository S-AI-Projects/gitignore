# R46-T001 — Dart.gitignore Fixtures and Classifications

## Template Under Test

Template: `Dart.gitignore`
Focus patterns:
- `.dart_tool/`
- `.packages`
- `build/`

Environment:
- Git: `git version 2.55.0`
- Python: `Python 3.14.7`

---

## 1. Fixture Inputs & Classifications

### Positive Fixtures (Expected: IGNORED)

| Fixture Input Path | Type | Expected Classification | Actual Classification | Responsible Rule | Line |
|---|---|---|---|---|---|
| `.dart_tool/config.json` | File in `.dart_tool/` | IGNORED | IGNORED | `.dart_tool/` | 5 |
| `.packages` | File | IGNORED | IGNORED | `.packages` | 6 |
| `build/output.txt` | File in root `build/` | IGNORED | IGNORED | `build/` | 7 |
| `sub/build/output.txt` | File in nested `build/` | IGNORED | IGNORED | `build/` | 7 |

### Negative Fixtures (Expected: NOT IGNORED — Near-Miss Names)

| Fixture Input Path | Type | Reason | Expected Classification | Actual Classification | Responsible Rule |
|---|---|---|---|---|---|
| `.dart_tool-file` | File | Trailing slash in `.dart_tool/` restricts to directories only | NOT IGNORED | NOT IGNORED | None (exit 1) |
| `.packages-backup` | File | Exact match required for `.packages` | NOT IGNORED | NOT IGNORED | None (exit 1) |
| `build.txt` | File | Trailing slash in `build/` restricts to directories only | NOT IGNORED | NOT IGNORED | None (exit 1) |
| `pubspec.lock` | File | Covered by template rule `pubspec.lock` | IGNORED | IGNORED | `pubspec.lock` (line 10) |

---

## 2. Tracked-File Verification (`git status --porcelain`)

The task explicitly verifies that Git ignore rules do not untrack already-tracked files, validated via `git status --porcelain`:

1. **Force-add and commit**:
   - `git add -f .packages` stages the ignored path.
   - `git commit -m "track .packages"` creates the tracked commit.

2. **Clean working tree verification**:
   - `git status --porcelain` returns empty (`""`), confirming no unexpected status flags on the tracked file.

3. **Modification detection**:
   - Modifying `.packages` causes `git status --porcelain` to report ` M .packages`.
   - The file is not hidden from status or ignored as untracked.

4. **Index check**:
   - `git check-ignore -v .packages` returns exit code 1 (index mode recognizes it is tracked and not ignored).
   - `git check-ignore -v --no-index .packages` returns exit code 0 and reports `.gitignore:6:.packages`.

5. **Untracked matching file comparison**:
   - Creating an untracked file `build/output.txt` results in empty output from `git status --porcelain build/output.txt`, confirming it is actively ignored.
