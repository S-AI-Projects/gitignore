# Task R46-T023: Negation Precedence in Global/STM32CubeIDE.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T023` (Task 3 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #23](https://github.com/S-AI-Projects/gitignore/issues/23)
- **Template**: `Global/STM32CubeIDE.gitignore`

---

## 1. Goal & Focus Patterns

Template: `Global/STM32CubeIDE.gitignore`. Use a temporary `.gitignore` that contains the selected rules and one explicit local negation example; demonstrate last-match behavior without adding a broad exception to the real template.

Focus patterns:
1. `*.log` (IDE build and session trace logs)
2. `Debug/` (Compiler output directory for debug builds)
3. `Release/` (Compiler output directory for release builds)

---

## 2. Negation Precedence & Last-Match Semantics

Git evaluates ignore rules sequentially from top to bottom. In Git's rule matching model, **the last matching pattern wins**. When an exclamation mark (`!`) prefix is used to negate an ignore pattern:

1. **Re-inclusion via Negation Order (`*.log` followed by `!important.log`)**:
   - When a broad rule `*.log` is placed first, followed by explicit negation `!important.log`:
     - Regular log files (e.g. `build.log`) match `*.log` and are ignored.
     - `important.log` matches the subsequent `!important.log` rule. Because the negation appears later in the file, it overrides `*.log`.
     - Result: `important.log` is re-included and remains visible in `git status --porcelain` (`?? important.log`).

2. **Negation Overridden by Subsequent Rule (`!important.log` followed by `*.log`)**:
   - If the negation pattern is placed *before* the broad rule:
     - When Git evaluates `important.log`, the later rule `*.log` overrides the earlier `!important.log`.
     - Result: `important.log` is ignored and does not appear in `git status`.

---

## 3. Fixture Verification

### A. Focus Pattern: `*.log`
- **Matching Fixtures (Ignored)**:
  - `ide_session.log`: Standard root log file (matches `.gitignore:19:*.log`).
  - `Core/Src/build.log`: Nested log file in source directory.
- **Near-Miss Fixtures (Remain Visible)**:
  - `logger.c`: Legitimate C source file sharing prefix `log`.
  - `Inc/logical_ops.h`: Header file containing `log`.
  - `ide.log.txt`: Text file ending in `.txt` rather than `.log`.

### B. Focus Pattern: `Debug/`
- **Matching Fixtures (Ignored)**:
  - `Debug/output.elf`: Binary executable in root `Debug/` folder.
  - `Core/Debug/module.o`: Object file in nested `Debug/` folder.
- **Near-Miss Fixtures (Remain Visible)**:
  - `Debug.c`: Source file named `Debug.c` (trailing slash ensures directories only are ignored).
  - `docs/Debug`: Regular file without trailing slash.
  - `Debugger/tracer.c`: Directory with `Debugger` prefix.

### C. Focus Pattern: `Release/`
- **Matching Fixtures (Ignored)**:
  - `Release/firmware.bin`: Binary firmware inside `Release/`.
  - `Subsystem/Release/app.hex`: Flash hex artifact inside nested `Release/`.
- **Near-Miss Fixtures (Remain Visible)**:
  - `Release_notes.txt`: Release notes documentation file.
  - `Inc/ReleaseConfig.h`: C header file.
  - `docs/Release`: Regular file without trailing slash.

---

## 4. Tracked File Behavior

- Files committed prior to applying ignore rules (e.g., `Debug/pre_existing_tracked_config.txt`) remain tracked.
- Modifying a pre-tracked file inside an ignored directory is correctly reported as `M Debug/pre_existing_tracked_config.txt` by `git status --porcelain`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T023/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T023_FORCE_FAIL=1 python3 work/R46-T023/check.py
```
