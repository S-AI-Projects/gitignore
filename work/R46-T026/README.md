# Task R46-T026: Path and Case Assumptions in Actionscript.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T026` (Task 6 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #26](https://github.com/S-AI-Projects/gitignore/issues/26)
- **Template**: `Actionscript.gitignore`

---

## 1. Goal & Focus Patterns

Template: `Actionscript.gitignore`. Test the selected rules with space-containing paths and case variants; record filesystem case behavior and `core.ignorecase` explicitly.

Focus patterns:
1. `bin-debug/` (Debug compiler output folder)
2. `bin-release/` (Release packaging output folder)
3. `[Oo]bj/` (Intermediate build object directory, case-bracketed)

---

## 2. Path and Case Analysis

### A. Space-Containing Paths
- In Git's ignore engine, space characters in file or directory paths (e.g. `Flash Games/Action Game/bin-debug/game.swf`) do **not** require escaping or quoting in `.gitignore` unless leading or trailing spaces are part of the pattern name.
- Unanchored rules like `bin-debug/` correctly match directories located inside parent folders containing whitespace.

### B. Case Sensitivity and Bracket Expressions (`[Oo]bj/`)
- **Filesystem Environment**:
  - Filesystem case-insensitive: `True`
  - Git `core.ignorecase`: `true`
- **Pattern Design**:
  - The pattern `[Oo]bj/` uses a POSIX character class `[Oo]` to explicitly match both lowercase `obj/` and titlecase `Obj/`.
  - This bracket expression ensures deterministic behavior across both case-sensitive platforms (Linux ext4) and case-insensitive platforms (macOS APFS / Windows NTFS).

---

## 3. Fixture Verification

### A. Focus Pattern: `bin-debug/`
- **Matching Fixtures**:
  - `bin-debug/app.swf`: Standard root output (`.gitignore:2:bin-debug/`).
  - `Flash Games/Action Game/bin-debug/game.swf`: Nested inside space-containing directories.
- **Near-Miss Fixtures (Visible)**:
  - `bin-debug.as`: ActionScript source file (trailing slash prevents matching non-directories).

### B. Focus Pattern: `bin-release/`
- **Matching Fixtures**:
  - `bin-release/app.air`: Standard root release folder (`.gitignore:3:bin-release/`).
  - `Client Builds/Release Candidate/bin-release/app.air`: Nested inside space-containing directories.
- **Near-Miss Fixtures (Visible)**:
  - `bin-release_notes.txt`: Release notes text file.

### C. Focus Pattern: `[Oo]bj/`
- **Matching Fixtures**:
  - `obj/intermediate.tmp`: Lowercase folder (`.gitignore:4:[Oo]bj/`).
  - `Obj/intermediate.tmp`: Uppercase folder (`.gitignore:4:[Oo]bj/`).
  - `Custom Components/UI Library/obj/cache.dat`: Space-containing directory hierarchy.
- **Near-Miss Fixtures (Visible)**:
  - `src/ObjectRenderer.as`: Legitimate ActionScript source class starting with Object.
  - `obj.as`: Regular file named `obj.as`.

---

## 4. Tracked File Behavior

- Files committed prior to applying ignore rules (e.g. `bin-debug/tracked_compiler_config.xml`) remain tracked.
- Modifying a pre-tracked file is reported as `M bin-debug/tracked_compiler_config.xml` by `git status --porcelain`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T026/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T026_FORCE_FAIL=1 python3 work/R46-T026/check.py
```
