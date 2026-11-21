#!/usr/bin/env python3
"""
Verification check for R46-T025 (Issue #25):
Template: Rust.gitignore
Focus patterns: debug, target, **/*.rs.bk

Goal:
Commit a matching fixture before applying the template, then compare it with an
untracked matching file; show why ignore rules do not untrack files.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T025/evidence.json, run.log, and README.md.
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
TEMPLATE = REPO_ROOT / "Rust.gitignore"
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


def define_fixtures() -> list[dict]:
    return [
        # --- Pattern 1: debug ---
        {
            "id": "debug-match-root",
            "focus_pattern": "debug",
            "path": "debug/app_binary",
            "expected_ignored": True,
            "expected_pattern": "debug",
            "description": "Legacy Cargo debug build output directory",
        },
        {
            "id": "debug-match-nested",
            "focus_pattern": "debug",
            "path": "output/debug/bin",
            "expected_ignored": True,
            "expected_pattern": "debug",
            "description": "Nested debug folder",
        },
        {
            "id": "debug-nonmatch-source",
            "focus_pattern": "debug",
            "path": "src/debug.rs",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate Rust source module debug.rs must remain visible",
        },
        {
            "id": "debug-nonmatch-prefix",
            "focus_pattern": "debug",
            "path": "debugger.rs",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: file sharing 'debug' prefix remains visible",
        },

        # --- Pattern 2: target ---
        {
            "id": "target-match-root",
            "focus_pattern": "target",
            "path": "target/release/my_bin",
            "expected_ignored": True,
            "expected_pattern": "target",
            "description": "Standard Cargo target directory at project root",
        },
        {
            "id": "target-match-nested",
            "focus_pattern": "target",
            "path": "crates/core/target/libcore.rlib",
            "expected_ignored": True,
            "expected_pattern": "target",
            "description": "Workspace crate target directory in subfolder",
        },
        {
            "id": "target-nonmatch-source",
            "focus_pattern": "target",
            "path": "src/target.rs",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate Rust source module target.rs must remain visible",
        },
        {
            "id": "target-nonmatch-subpath",
            "focus_pattern": "target",
            "path": "src/targeting/utils.rs",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: directory starting with 'targeting' remains visible",
        },

        # --- Pattern 3: **/*.rs.bk ---
        {
            "id": "rsbk-match-root",
            "focus_pattern": "**/*.rs.bk",
            "path": "main.rs.bk",
            "expected_ignored": True,
            "expected_pattern": "**/*.rs.bk",
            "description": "rustfmt backup file at repository root",
        },
        {
            "id": "rsbk-match-nested",
            "focus_pattern": "**/*.rs.bk",
            "path": "src/lib.rs.bk",
            "expected_ignored": True,
            "expected_pattern": "**/*.rs.bk",
            "description": "rustfmt backup file in nested source directory",
        },
        {
            "id": "rsbk-match-deep",
            "focus_pattern": "**/*.rs.bk",
            "path": "crates/ui/src/components/button.rs.bk",
            "expected_ignored": True,
            "expected_pattern": "**/*.rs.bk",
            "description": "Deeply nested rustfmt backup file matched by leading **/",
        },
        {
            "id": "rsbk-nonmatch-real-source",
            "focus_pattern": "**/*.rs.bk",
            "path": "src/main.rs",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate Rust source file main.rs must never be ignored",
        },
        {
            "id": "rsbk-nonmatch-bak",
            "focus_pattern": "**/*.rs.bk",
            "path": "src/main.rs.bak",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: general editor backup .rs.bak is distinct from rustfmt .rs.bk",
        },
    ]


def run_tracked_vs_untracked_comparison(template_text: str) -> dict:
    """Compare a pre-committed matching file with an untracked matching file."""
    with tempfile.TemporaryDirectory(prefix="rust-tracked-demo-") as tmpdir:
        repo = Path(tmpdir)
        run_command(["git", "init"], repo)
        run_command(["git", "config", "user.name", "Tracked Checker"], repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], repo)

        # Step 1: Pre-commit legitimate files before ignore rules exist
        tracked_matching = repo / "target" / "pre_committed_artifact.txt"
        tracked_matching.parent.mkdir(parents=True, exist_ok=True)
        tracked_matching.write_text("pre-existing tracked content\n", encoding="utf-8")

        run_command(["git", "add", "target/pre_committed_artifact.txt"], repo)
        run_command(["git", "commit", "-m", "Commit artifact before ignore template"], repo)

        # Step 2: Install ignore template
        (repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], repo)
        run_command(["git", "commit", "-m", "Install Rust .gitignore template"], repo)

        # Step 3: Create untracked matching file
        untracked_matching = repo / "target" / "untracked_artifact.txt"
        untracked_matching.write_text("untracked content\n", encoding="utf-8")

        # Step 4: Inspect with git check-ignore
        rc_tr, out_tr, _ = run_command(["git", "check-ignore", "-v", "--no-index", "target/pre_committed_artifact.txt"], repo)
        rc_un, out_un, _ = run_command(["git", "check-ignore", "-v", "--no-index", "target/untracked_artifact.txt"], repo)

        # Step 5: Check git status --porcelain
        _, st_initial, _ = run_command(["git", "status", "--porcelain"], repo)

        # Step 6: Modify the pre-committed tracked file
        tracked_matching.write_text("modified tracked content\n", encoding="utf-8")
        _, st_after_edit, _ = run_command(["git", "status", "--porcelain"], repo)

        tracked_remains_tracked = "M target/pre_committed_artifact.txt" in st_after_edit
        untracked_remains_hidden = "untracked_artifact.txt" not in st_after_edit

        return {
            "pre_committed_file": "target/pre_committed_artifact.txt",
            "untracked_file": "target/untracked_artifact.txt",
            "check_ignore_pre_committed": {
                "exit_code": rc_tr,
                "matches_rule": (rc_tr == 0),
                "output": out_tr,
            },
            "check_ignore_untracked": {
                "exit_code": rc_un,
                "matches_rule": (rc_un == 0),
                "output": out_un,
            },
            "status_before_edit": st_initial.strip(),
            "status_after_edit": st_after_edit.strip(),
            "tracked_remains_tracked": tracked_remains_tracked,
            "untracked_remains_hidden": untracked_remains_hidden,
            "passed": tracked_remains_tracked and untracked_remains_hidden,
            "explanation": (
                "Git ignore rules (.gitignore) only prevent UNTRACKED files from being added to the Git index. "
                "Files that were already committed/tracked in the index before the ignore rule was installed "
                "remain fully tracked by Git. While `git check-ignore` matches both files, `git status --porcelain` "
                "continues monitoring changes to the tracked file ('M target/pre_committed_artifact.txt') while "
                "completely hiding the untracked file."
            ),
        }


def main() -> None:
    force_fail = os.environ.get("R46_T025_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T025 Verification Check: Rust.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures...")
    print("----------------------------------------------------------------------")

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="rust-verify-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install Rust .gitignore template"], tmp_repo)

        for tc in fixtures:
            rel_path = tc["path"]
            file_path = tmp_repo / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"content for {rel_path}\n", encoding="utf-8")

            rc, stdout, stderr = run_command(
                ["git", "check-ignore", "-v", "--no-index", rel_path],
                tmp_repo,
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

            _, st_out, _ = run_command(["git", "status", "--porcelain", rel_path], tmp_repo)
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

            if force_fail and tc["id"] == "debug-match-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<28} | Path: {rel_path:<36} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern}"
            )

            record = {
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": rel_path,
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
            actual_results.append(record)

            if not passed:
                failures.append(f"{tc['id']} ({rel_path}): assertion failed")

            if file_path.exists():
                file_path.unlink()

    # Tracked vs Untracked demonstration
    print("----------------------------------------------------------------------")
    print("Testing Tracked vs Untracked file comparison...")
    tracked_demo = run_tracked_vs_untracked_comparison(template_text)
    tracked_demo_ok = tracked_demo["passed"]
    print(f"[{'PASS' if tracked_demo_ok else 'FAIL'}] Tracked vs Untracked demonstration: pre-committed target file remains tracked (M), untracked file hidden")
    if not tracked_demo_ok:
        failures.append("Tracked vs untracked comparison failed")

    # Structure evidence payload
    all_passed = len(failures) == 0
    evidence = {
        "task_id": "R46-T025",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "Rust.gitignore",
        "focus_patterns": ["debug", "target", "**/*.rs.bk"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "tracked_vs_untracked_demonstration": tracked_demo,
        "test_cases": actual_results,
        "summary": {
            "total_checks": len(fixtures) + 1,
            "passed": sum(1 for r in actual_results if r["passed"]) + (1 if tracked_demo_ok else 0),
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
        f"Command: python3 work/R46-T025/check.py\n"
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
    readme_content = f"""# Task R46-T025: Explain Already-Tracked Files in Rust.gitignore

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
     - `git check-ignore -v --no-index target/pre_committed_artifact.txt` reports that the path matches `.gitignore:{pattern_lines.get('target')}:target`.
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
