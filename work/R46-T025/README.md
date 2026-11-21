# Task R46-T025: Explain Already-Tracked Files in Rust.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T025` (Task 5 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #25](https://github.com/S-AI-Projects/gitignore/issues/25)
- **Template**: `Rust.gitignore`

---

## 1. Goal & Focus Patterns

Template: `Rust.gitignore`. Commit a matching fixture before applying the template, then compare it with an untracked matching file; demonstrate why ignore rules do not untrack files.

Focus patterns:
1. `debug` (Legacy Cargo debug build output directory)
2. `target` (Standard Cargo compilation artifacts directory)
3. `**/*.rs.bk` (rustfmt backup files)

---

## 2. Tracked vs. Untracked File Semantics

In Git's architecture:
1. **Scope of `.gitignore`**:
   - Ignore patterns only apply to **untracked** files to prevent them from accidentally being added to the staging index.
   - An ignore rule does **not** untrack a file that has already been staged or committed.

2. **Demonstration**:
   - When `target/pre_committed_artifact.txt` is committed to the repository *before* `Rust.gitignore` is installed:
     - `git check-ignore -v --no-index target/pre_committed_artifact.txt` reports that the path matches `.gitignore:5:target`.
     - However, when the file is modified, `git status --porcelain` still reports `M target/pre_committed_artifact.txt`. The file remains fully tracked and versioned.
   - In contrast, when `target/untracked_artifact.txt` is created *after* the template is installed, Git ignores it completely, and `git status --porcelain` remains clean.
   - **How to stop tracking**: To untrack a committed file without deleting it from disk, a developer must explicitly run `git rm --cached <file>`.

---

## 3. Fixture Verification

### A. Focus Pattern: `debug`
- **Matching Fixtures**:
  - `debug/app_binary`: Root debug folder.
  - `target/debug/build`: Nested debug directory.
- **Near-Miss Fixtures (Visible)**:
  - `src/debug.rs`: Legitimate Rust source code file.
  - `debugger.rs`: Legitimate source file sharing prefix.

### B. Focus Pattern: `target`
- **Matching Fixtures**:
  - `target/release/my_bin`: Cargo target release artifact.
  - `crates/core/target/libcore.rlib`: Subcrate target directory.
- **Near-Miss Fixtures (Visible)**:
  - `src/target.rs`: Legitimate Rust source file.
  - `src/targeting/utils.rs`: Legitimate source subdirectory.

### C. Focus Pattern: `**/*.rs.bk`
- **Matching Fixtures**:
  - `main.rs.bk`: Root rustfmt backup file.
  - `src/lib.rs.bk`: Nested rustfmt backup file.
  - `crates/ui/src/components/button.rs.bk`: Deeply nested backup file.
- **Near-Miss Fixtures (Visible)**:
  - `src/main.rs`: Legitimate Rust source file (must never be ignored!).
  - `src/main.rs.bak`: Non-rustfmt backup file ending in `.bak`.

---

## 4. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T025/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T025_FORCE_FAIL=1 python3 work/R46-T025/check.py
```
