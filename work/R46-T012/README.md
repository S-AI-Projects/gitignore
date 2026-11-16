# Task R46-T012: Nested Path Matching in ecu.test.gitignore

## Focus Patterns
- `.workspace/ETdrive.xml`
- `.workspace/favorites.xml`
- `.workspace/filters.xml`

## Anchoring & Nested Path Matching Analysis

In Git ignore syntax (documented in `gitignore(5)`):
- If a pattern does not contain a slash `/` (excluding any trailing slash), Git matches the pattern at any directory depth.
- If a pattern contains a slash `/` within the pattern (such as `.workspace/ETdrive.xml`), Git treats the pattern as relative to the location of the `.gitignore` file itself (i.e. anchored to the repository root when `.gitignore` is at the root).

### 1. Root Level vs Nested Directories
- **Repository Root**:
  - `.workspace/ETdrive.xml`: **Ignored** (matches rule `.workspace/ETdrive.xml`).
  - `.workspace/favorites.xml`: **Ignored** (matches rule `.workspace/favorites.xml`).
  - `.workspace/filters.xml`: **Ignored** (matches rule `.workspace/filters.xml`).
- **Nested Directory 1 (`subproject/.workspace/`)**:
  - `subproject/.workspace/ETdrive.xml`: **Not Ignored**. The anchored pattern `.workspace/ETdrive.xml` does not match at deeper directory levels.
  - `subproject/.workspace/favorites.xml`: **Not Ignored**.
  - `subproject/.workspace/filters.xml`: **Not Ignored**.
- **Nested Directory 2 (`tests/integration/.workspace/`)**:
  - `tests/integration/.workspace/ETdrive.xml`: **Not Ignored**.
  - `tests/integration/.workspace/favorites.xml`: **Not Ignored**.
  - `tests/integration/.workspace/filters.xml`: **Not Ignored**.
- **Root Equivalent Basename (`ETdrive.xml`)**:
  - `ETdrive.xml`: **Not Ignored**. Without the `.workspace/` path prefix, the file does not match.

### 2. Comparison with Unanchored Patterns
By contrast, patterns in `ecu.test.gitignore` that do not contain a slash, such as `*.arxml` and `TestReports`:
- `test.arxml`: Ignored at root.
- `subproject/test.arxml`: Ignored in nested directory.
- `tests/integration/test.arxml`: Ignored in deep nested directory.

## Tracked Files Behavior
Files already tracked by Git prior to applying the template (e.g. pre-committed `.workspace/ETdrive.xml`) remain tracked and monitored for modifications. `git status --porcelain` correctly reports modifications (`M .workspace/ETdrive.xml`).

## Automated Verification
Run the verification check:
```bash
python3 work/R46-T012/check.py
```
To test error detection and non-zero exit:
```bash
R46_T012_FORCE_FAIL=1 python3 work/R46-T012/check.py
```
