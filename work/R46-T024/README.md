# Task R46-T024: Distinguish Directories from Files in C.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T024` (Task 4 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #24](https://github.com/S-AI-Projects/gitignore/issues/24)
- **Template**: `C.gitignore`

---

## 1. Goal & Focus Patterns

Template: `C.gitignore`. Create file and directory fixtures with the same basename in separate repositories; explain the effect of a trailing slash in the selected patterns.

Focus patterns:
1. `*.d` (Compiler dependency tracking prerequisites)
2. `*.o` (Compiled binary object files)
3. `*.ko` (Linux kernel object modules)

---

## 2. Directory vs. File Trailing Slash Semantics

In Git's ignore pattern syntax:
1. **Patterns Without Trailing Slash (`*.d`, `*.o`, `*.ko`)**:
   - When a pattern does not end with a forward slash `/`, Git matches **both regular files and directories** matching the pattern.
   - **Repository 1 (Regular Files)**: `main.d`, `main.o`, and `driver.ko` are ignored.
   - **Repository 2 (Directories with identical basenames)**: `main.d/`, `main.o/`, and `driver.ko/` are also matched and ignored.

2. **Patterns With Trailing Slash (`*.d/` or `*.dSYM/`)**:
   - A trailing slash specifies that the pattern matches **only directories**.
   - **Repository 3 (Demonstration)**:
     - Under rule `*.d/`, directory `config.d/` is **IGNORED**.
     - Regular file `main.d` is **NOT IGNORED** and remains visible in `git status` as `?? main.d`.
   - In `C.gitignore`, patterns like `*.dSYM/` (line 40) explicitly use a trailing slash because macOS debug symbol bundles are directory bundles, whereas `*.d`, `*.o`, and `*.ko` intentionally omit the trailing slash to ignore object artifacts regardless of whether a build system creates them as files or directories.

---

## 3. Fixture Verification

### A. Focus Pattern: `*.d`
- **Matching Fixtures**:
  - `main.d` (file): Root dependency file (`.gitignore:2:*.d`).
  - `src/utils.d` (file): Nested dependency file.
  - `main.d/` (directory in Repo 2): Directory with matching basename is also ignored.
- **Near-Miss Fixtures (Visible)**:
  - `main.c`: Legitimate C source code file (must remain visible in version control).
  - `main.d.bak`: Backup file ending in `.bak`.

### B. Focus Pattern: `*.o`
- **Matching Fixtures**:
  - `main.o` (file): Root object file (`.gitignore:5:*.o`).
  - `build/objects/engine.o` (file): Nested object file.
  - `main.o/` (directory in Repo 2): Directory with matching basename is ignored.
- **Near-Miss Fixtures (Visible)**:
  - `main.h`: Legitimate C header file.
  - `main.o.txt`: Text file ending in `.txt`.

### C. Focus Pattern: `*.ko`
- **Matching Fixtures**:
  - `driver.ko` (file): Linux kernel module (`.gitignore:6:*.ko`).
  - `drivers/net/nic.ko` (file): Nested kernel module.
  - `driver.ko/` (directory in Repo 2): Directory with matching basename is ignored.
- **Near-Miss Fixtures (Visible)**:
  - `driver.c`: Kernel module source file (must remain visible).
  - `driver.ko.symvers`: Module symbols metadata file.

---

## 4. Tracked File Behavior

- Files tracked before applying ignore rules (e.g., `main.o` pre-tracked) remain tracked.
- Modifying a pre-tracked file is reported as `M main.o` by `git status --porcelain`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T024/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T024_FORCE_FAIL=1 python3 work/R46-T024/check.py
```
