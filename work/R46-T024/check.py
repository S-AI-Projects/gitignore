#!/usr/bin/env python3
"""
Verification check for R46-T024 (Issue #24):
Template: C.gitignore
Focus patterns: *.d, *.o, *.ko

Goal:
Create file and directory fixtures with the same basename in separate repositories;
explain the effect of a trailing slash in the selected patterns.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T024/evidence.json, run.log, and README.md.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "C.gitignore"
EVIDENCE_FILE = TASK_DIR / "evidence.json"
TOOL_VERSIONS_FILE = TASK_DIR / "tool_versions.txt"
LOG_FILE = TASK_DIR / "run.log"
README_FILE = TASK_DIR / "README.md"


def run_command(cmd: list[str], cwd: Path | str) -> tuple[int, str, str]:
    res = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def get_tool_versions() -> dict[str, str]:
    git_rc, git_ver, _ = run_command(["git", "--version"], REPO_ROOT)
    return {
        "git": git_ver if git_rc == 0 else "unknown",
        "python": sys.version.replace("\n", " "),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
    }


def get_template_pattern_lines(template_text: str) -> dict[str, int]:
    lines = {}
    for idx, line in enumerate(template_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines[stripped] = idx
    return lines


def define_file_fixtures() -> list[dict]:
    """Test regular files matching or near-missing the focus patterns."""
    return [
        # --- Pattern 1: *.d (Dependency files) ---
        {
            "id": "d-file-match-root",
            "focus_pattern": "*.d",
            "path": "main.d",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.d",
            "description": "Compiler-generated dependency file at root",
        },
        {
            "id": "d-file-match-nested",
            "focus_pattern": "*.d",
            "path": "src/utils.d",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.d",
            "description": "Nested dependency file in source subdirectory",
        },
        {
            "id": "d-file-nonmatch-c-source",
            "focus_pattern": "*.d",
            "path": "main.c",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate C source code file must remain visible",
        },
        {
            "id": "d-file-nonmatch-bak",
            "focus_pattern": "*.d",
            "path": "main.d.bak",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: backup file ending in .bak is not matched",
        },

        # --- Pattern 2: *.o (Object files) ---
        {
            "id": "o-file-match-root",
            "focus_pattern": "*.o",
            "path": "main.o",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.o",
            "description": "Compiled object file at root",
        },
        {
            "id": "o-file-match-nested",
            "focus_pattern": "*.o",
            "path": "build/objects/engine.o",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.o",
            "description": "Object file in nested build directory",
        },
        {
            "id": "o-file-nonmatch-header",
            "focus_pattern": "*.o",
            "path": "main.h",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate C header file must remain visible",
        },
        {
            "id": "o-file-nonmatch-txt",
            "focus_pattern": "*.o",
            "path": "main.o.txt",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: text file ending in .txt is not matched by *.o",
        },

        # --- Pattern 3: *.ko (Kernel modules) ---
        {
            "id": "ko-file-match-root",
            "focus_pattern": "*.ko",
            "path": "driver.ko",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.ko",
            "description": "Compiled Linux kernel module file",
        },
        {
            "id": "ko-file-match-nested",
            "focus_pattern": "*.ko",
            "path": "drivers/net/nic.ko",
            "type": "file",
            "expected_ignored": True,
            "expected_pattern": "*.ko",
            "description": "Kernel module in nested drivers subdirectory",
        },
        {
            "id": "ko-file-nonmatch-symvers",
            "focus_pattern": "*.ko",
            "path": "driver.ko.symvers",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: module symbols file is not matched by *.ko",
        },
        {
            "id": "ko-file-nonmatch-c-source",
            "focus_pattern": "*.ko",
            "path": "driver.c",
            "type": "file",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Kernel module source file driver.c must remain visible",
        },
    ]


def define_directory_fixtures() -> list[dict]:
    """Test directory fixtures sharing the exact same basenames in a separate repo."""
    return [
        {
            "id": "d-dir-match-root",
            "focus_pattern": "*.d",
            "path": "main.d",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.d",
            "description": "Directory named 'main.d': *.d has no trailing slash, so it matches directories too",
        },
        {
            "id": "d-dir-match-nested",
            "focus_pattern": "*.d",
            "path": "src/utils.d",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.d",
            "description": "Nested directory named 'utils.d': matches unanchored *.d pattern",
        },
        {
            "id": "o-dir-match-root",
            "focus_pattern": "*.o",
            "path": "main.o",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.o",
            "description": "Directory named 'main.o': *.o matches directories because it has no trailing slash",
        },
        {
            "id": "o-dir-match-nested",
            "focus_pattern": "*.o",
            "path": "build/objects/engine.o",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.o",
            "description": "Nested directory named 'engine.o' is matched by *.o",
        },
        {
            "id": "ko-dir-match-root",
            "focus_pattern": "*.ko",
            "path": "driver.ko",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.ko",
            "description": "Directory named 'driver.ko' is matched by *.ko",
        },
        {
            "id": "ko-dir-match-nested",
            "focus_pattern": "*.ko",
            "path": "drivers/net/nic.ko",
            "type": "directory",
            "expected_ignored": True,
            "expected_pattern": "*.ko",
            "description": "Nested directory named 'nic.ko' is matched by *.ko",
        },
    ]


def run_trailing_slash_contrast() -> dict:
    """Demonstrate the effect of a trailing slash in a separate isolated repository.
    Rule: *.d/ (with trailing slash)
    - Directory 'config.d/' -> IGNORED
    - Regular file 'main.d' -> NOT IGNORED (visible)
    """
    with tempfile.TemporaryDirectory(prefix="c-trailing-slash-") as tmpdir:
        repo = Path(tmpdir)
        run_command(["git", "init"], repo)
        (repo / ".gitignore").write_text("*.d/\n", encoding="utf-8")
        run_command(["git", "add", ".gitignore"], repo)
        run_command(["git", "commit", "-m", "Install trailing slash rule"], repo)

        # 1. Create directory config.d containing a file
        dir_path = repo / "config.d"
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / "settings.conf").write_text("config=true\n", encoding="utf-8")

        # 2. Create regular file main.d
        file_path = repo / "main.d"
        file_path.write_text("deps output\n", encoding="utf-8")

        rc_dir, out_dir, _ = run_command(["git", "check-ignore", "-v", "--no-index", "config.d/"], repo)
        rc_file, out_file, _ = run_command(["git", "check-ignore", "-v", "--no-index", "main.d"], repo)
        _, st_out, _ = run_command(["git", "status", "--porcelain"], repo)

        return {
            "tested_rule": "*.d/",
            "directory_check": {
                "path": "config.d/",
                "ignored": (rc_dir == 0),
                "pattern": out_dir.split("\t")[0].split(":")[2] if rc_dir == 0 else None,
                "passed": (rc_dir == 0),
            },
            "file_check": {
                "path": "main.d",
                "ignored": (rc_file == 0),
                "passed": (rc_file == 1),  # Must NOT be ignored because rule has trailing slash!
            },
            "porcelain_status": st_out.strip(),
            "explanation": (
                "When a pattern has a trailing slash (e.g. *.d/), Git restricts matching exclusively "
                "to directories. Therefore, directory 'config.d/' is ignored, but regular file 'main.d' "
                "remains unignored and visible in status as '?? main.d'. In contrast, C.gitignore uses "
                "bare patterns (*.d, *.o, *.ko) without trailing slashes, which match both regular files "
                "and directories sharing the same basename."
            ),
            "passed": (rc_dir == 0) and (rc_file == 1) and ("?? main.d" in st_out),
        }


def main() -> None:
    force_fail = os.environ.get("R46_T024_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    file_fixtures = define_file_fixtures()
    dir_fixtures = define_directory_fixtures()

    print("======================================================================")
    print(" R46-T024 Verification Check: C.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print("----------------------------------------------------------------------")

    failures = []
    file_results = []
    dir_results = []

    # ========================================================================
    # Repository 1: Regular File Fixtures
    # ========================================================================
    print(f"[*] Repository 1: Testing {len(file_fixtures)} regular file fixtures...")
    with tempfile.TemporaryDirectory(prefix="c-files-repo-") as tmpdir1:
        repo1 = Path(tmpdir1)
        run_command(["git", "init"], repo1)
        run_command(["git", "config", "user.name", "Check Runner"], repo1)
        run_command(["git", "config", "user.email", "checker@example.invalid"], repo1)

        (repo1 / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], repo1)
        run_command(["git", "commit", "-m", "Install C.gitignore template"], repo1)

        for tc in file_fixtures:
            rel_path = tc["path"]
            file_path = repo1 / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"content for {rel_path}\n", encoding="utf-8")

            rc, stdout, stderr = run_command(
                ["git", "check-ignore", "-v", "--no-index", rel_path],
                repo1,
            )

            actual_ignored = (rc == 0)
            actual_rule_line = None
            actual_pattern = None

            if actual_ignored and stdout:
                parts = stdout.split("\t")
                rule_source = parts[0]
                rule_parts = rule_source.split(":")
                if len(rule_parts) >= 3:
                    actual_rule_line = int(rule_parts[1])
                    actual_pattern = rule_parts[2]

            _, st_out, _ = run_command(["git", "status", "--porcelain", rel_path], repo1)
            porcelain_status = st_out.strip()

            if actual_ignored:
                porcelain_ok = (porcelain_status == "")
            else:
                porcelain_ok = porcelain_status.startswith("??")

            passed = (actual_ignored == tc["expected_ignored"])
            if tc["expected_ignored"]:
                if actual_pattern != tc["expected_pattern"]:
                    passed = False
                expected_line = pattern_lines.get(tc["expected_pattern"])
                if expected_line is not None and actual_rule_line != expected_line:
                    passed = False

            if not porcelain_ok:
                passed = False

            if force_fail and tc["id"] == "d-file-match-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] [FILE] {tc['id']:<28} | Path: {rel_path:<26} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern}"
            )

            record = {
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": rel_path,
                "type": "file",
                "description": tc["description"],
                "expected": {
                    "ignored": tc["expected_ignored"],
                    "pattern": tc["expected_pattern"],
                    "line": pattern_lines.get(tc["expected_pattern"]),
                },
                "actual": {
                    "ignored": actual_ignored,
                    "returncode": rc,
                    "pattern": actual_pattern,
                    "rule_line": actual_rule_line,
                    "porcelain_status": porcelain_status,
                    "raw_check_ignore": stdout,
                },
                "passed": passed,
            }
            file_results.append(record)

            if not passed:
                failures.append(f"{tc['id']} ({rel_path}): assertion failed")

            if file_path.exists():
                file_path.unlink()

        # Tracked file behavior in Repo 1
        tracked_rel = "main.o"
        tracked_path = repo1 / tracked_rel
        tracked_path.write_text("initial object\n", encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], repo1)
        run_command(["git", "commit", "-m", "Track pre-existing object file"], repo1)

        tracked_path.write_text("modified object\n", encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], repo1)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain main.o' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked main.o modification was not reported by status")

    # ========================================================================
    # Repository 2: Directory Fixtures (Same Basenames)
    # ========================================================================
    print("----------------------------------------------------------------------")
    print(f"[*] Repository 2: Testing {len(dir_fixtures)} directory fixtures with identical basenames...")
    with tempfile.TemporaryDirectory(prefix="c-dirs-repo-") as tmpdir2:
        repo2 = Path(tmpdir2)
        run_command(["git", "init"], repo2)
        (repo2 / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], repo2)
        run_command(["git", "commit", "-m", "Install C.gitignore template"], repo2)

        for tc in dir_fixtures:
            rel_path = tc["path"]
            dir_path = repo2 / rel_path
            dir_path.mkdir(parents=True, exist_ok=True)
            # Create dummy payload file inside directory so git detects directory
            (dir_path / "payload.tmp").write_text("dir content\n", encoding="utf-8")

            # Check directory path (with trailing slash)
            rc, stdout, stderr = run_command(
                ["git", "check-ignore", "-v", "--no-index", f"{rel_path}/"],
                repo2,
            )

            actual_ignored = (rc == 0)
            actual_rule_line = None
            actual_pattern = None

            if actual_ignored and stdout:
                parts = stdout.split("\t")
                rule_source = parts[0]
                rule_parts = rule_source.split(":")
                if len(rule_parts) >= 3:
                    actual_rule_line = int(rule_parts[1])
                    actual_pattern = rule_parts[2]

            _, st_out, _ = run_command(["git", "status", "--porcelain", rel_path], repo2)
            porcelain_status = st_out.strip()

            passed = (actual_ignored == tc["expected_ignored"])
            if tc["expected_ignored"]:
                if actual_pattern != tc["expected_pattern"]:
                    passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] [DIR]  {tc['id']:<28} | Path: {rel_path + '/':<26} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern}"
            )

            record = {
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": f"{rel_path}/",
                "type": "directory",
                "description": tc["description"],
                "expected": {
                    "ignored": tc["expected_ignored"],
                    "pattern": tc["expected_pattern"],
                    "line": pattern_lines.get(tc["expected_pattern"]),
                },
                "actual": {
                    "ignored": actual_ignored,
                    "returncode": rc,
                    "pattern": actual_pattern,
                    "rule_line": actual_rule_line,
                    "porcelain_status": porcelain_status,
                    "raw_check_ignore": stdout,
                },
                "passed": passed,
            }
            dir_results.append(record)

            if not passed:
                failures.append(f"{tc['id']} ({rel_path}/): directory assertion failed")

    # ========================================================================
    # Repository 3: Trailing Slash Semantic Contrast
    # ========================================================================
    print("----------------------------------------------------------------------")
    print("[*] Repository 3: Testing trailing slash semantic contrast (*.d/)...")
    contrast_results = run_trailing_slash_contrast()
    contrast_ok = contrast_results["passed"]
    print(f"[{'PASS' if contrast_ok else 'FAIL'}] Trailing slash contrast: directory config.d/ ignored, regular file main.d visible")
    if not contrast_ok:
        failures.append("Trailing slash semantic contrast failed")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T024",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "C.gitignore",
        "focus_patterns": ["*.d", "*.o", "*.ko"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "trailing_slash_semantics": {
            "patterns_without_trailing_slash": {
                "patterns": ["*.d", "*.o", "*.ko"],
                "behavior": (
                    "In Gitignore syntax, patterns without a trailing slash match both regular files "
                    "and directories sharing the same extension. Hence, both file main.o and directory "
                    "main.o/ are matched and ignored."
                ),
            },
            "patterns_with_trailing_slash": {
                "demonstration": contrast_results,
                "behavior": (
                    "Appending a trailing slash (e.g. *.d/ or *.dSYM/) restricts the pattern exclusively "
                    "to directory matching. Regular files sharing the name remain unignored and visible."
                ),
            },
        },
        "tracked_file_check": {
            "path": "main.o",
            "description": "Pre-tracked main.o modification remains tracked and visible in status --porcelain",
            "porcelain_status": tracked_st_out,
            "passed": tracked_modified_visible,
        },
        "repository_1_file_fixtures": file_results,
        "repository_2_directory_fixtures": dir_results,
        "summary": {
            "total_checks": len(file_fixtures) + len(dir_fixtures) + 2,
            "passed": sum(1 for r in file_results if r["passed"]) + sum(1 for r in dir_results if r["passed"]) + (1 if tracked_modified_visible else 0) + (1 if contrast_ok else 0),
            "failed": len(failures),
            "all_passed": all_passed,
        },
    }

    # Write evidence.json
    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"[+] Saved structured evidence to {EVIDENCE_FILE}")

    # Write tool_versions.txt
    TOOL_VERSIONS_FILE.write_text(
        f"Git: {tool_versions['git']}\n"
        f"Python: {tool_versions['python']}\n"
        f"Platform: {tool_versions['platform']}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved tool versions to {TOOL_VERSIONS_FILE}")

    # Write run.log
    LOG_FILE.write_text(
        f"Command: python3 work/R46-T024/check.py\n"
        f"Git: {tool_versions['git']}\n"
        f"Python: {tool_versions['python']}\n"
        f"Platform: {tool_versions['platform']}\n"
        f"Total checks: {evidence['summary']['total_checks']}\n"
        f"Passed: {evidence['summary']['passed']}\n"
        f"Failed: {evidence['summary']['failed']}\n"
        f"Status: {'PASS' if all_passed else 'FAIL'}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved run log to {LOG_FILE}")

    # Write README.md
    readme_content = f"""# Task R46-T024: Distinguish Directories from Files in C.gitignore

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
  - `main.d` (file): Root dependency file (`.gitignore:{pattern_lines.get('*.d')}:*.d`).
  - `src/utils.d` (file): Nested dependency file.
  - `main.d/` (directory in Repo 2): Directory with matching basename is also ignored.
- **Near-Miss Fixtures (Visible)**:
  - `main.c`: Legitimate C source code file (must remain visible in version control).
  - `main.d.bak`: Backup file ending in `.bak`.

### B. Focus Pattern: `*.o`
- **Matching Fixtures**:
  - `main.o` (file): Root object file (`.gitignore:{pattern_lines.get('*.o')}:*.o`).
  - `build/objects/engine.o` (file): Nested object file.
  - `main.o/` (directory in Repo 2): Directory with matching basename is ignored.
- **Near-Miss Fixtures (Visible)**:
  - `main.h`: Legitimate C header file.
  - `main.o.txt`: Text file ending in `.txt`.

### C. Focus Pattern: `*.ko`
- **Matching Fixtures**:
  - `driver.ko` (file): Linux kernel module (`.gitignore:{pattern_lines.get('*.ko')}:*.ko`).
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
"""
    README_FILE.write_text(readme_content, encoding="utf-8")
    print(f"[+] Saved README documentation to {README_FILE}")

    if failures:
        print("\n[!] ASSERTION FAILURES OCCURRED:")
        for f in failures:
            print(f"    - {f}")
        sys.exit(1)
    else:
        print(f"\n[PASS] All {evidence['summary']['total_checks']} checks passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
