#!/usr/bin/env python3
"""
Verification check for R46-T026 (Issue #26):
Template: Actionscript.gitignore
Focus patterns: bin-debug/, bin-release/, [Oo]bj/

Goal:
Test the selected rules with space-containing paths and case variants;
record filesystem case behavior and core.ignorecase explicitly.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T026/evidence.json, run.log, and README.md.
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
TEMPLATE = REPO_ROOT / "Actionscript.gitignore"
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


def detect_filesystem_case_sensitivity(tmp_repo: Path) -> dict[str, bool | str]:
    probe_upper = tmp_repo / "CaseTestProbe.txt"
    probe_lower = tmp_repo / "casetestprobe.txt"
    probe_upper.write_text("probe\n", encoding="utf-8")
    is_case_insensitive = probe_lower.exists()
    probe_upper.unlink()

    rc, ignorecase_config, _ = run_command(["git", "config", "core.ignorecase"], tmp_repo)

    return {
        "filesystem_case_insensitive": is_case_insensitive,
        "git_core_ignorecase": ignorecase_config.strip() if rc == 0 else "unset",
    }


def define_fixtures() -> list[dict]:
    return [
        # --- Pattern 1: bin-debug/ ---
        {
            "id": "bindebug-match-root",
            "focus_pattern": "bin-debug/",
            "path": "bin-debug/app.swf",
            "is_space_path": False,
            "expected_ignored": True,
            "expected_pattern": "bin-debug/",
            "description": "Standard debug output directory",
        },
        {
            "id": "bindebug-match-space-path",
            "focus_pattern": "bin-debug/",
            "path": "Flash Games/Action Game/bin-debug/game.swf",
            "is_space_path": True,
            "expected_ignored": True,
            "expected_pattern": "bin-debug/",
            "description": "Nested path containing spaces in directory names",
        },
        {
            "id": "bindebug-nonmatch-source",
            "focus_pattern": "bin-debug/",
            "path": "bin-debug.as",
            "is_space_path": False,
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: ActionScript source file bin-debug.as remains visible",
        },

        # --- Pattern 2: bin-release/ ---
        {
            "id": "binrelease-match-root",
            "focus_pattern": "bin-release/",
            "path": "bin-release/app.air",
            "is_space_path": False,
            "expected_ignored": True,
            "expected_pattern": "bin-release/",
            "description": "Standard release packaging directory",
        },
        {
            "id": "binrelease-match-space-path",
            "focus_pattern": "bin-release/",
            "path": "Client Builds/Release Candidate/bin-release/app.air",
            "is_space_path": True,
            "expected_ignored": True,
            "expected_pattern": "bin-release/",
            "description": "Deeply nested release directory with multiple spaces in path",
        },
        {
            "id": "binrelease-nonmatch-notes",
            "focus_pattern": "bin-release/",
            "path": "bin-release_notes.txt",
            "is_space_path": False,
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: documentation file bin-release_notes.txt remains visible",
        },

        # --- Pattern 3: [Oo]bj/ ---
        {
            "id": "obj-match-lowercase",
            "focus_pattern": "[Oo]bj/",
            "path": "obj/intermediate.tmp",
            "is_space_path": False,
            "expected_ignored": True,
            "expected_pattern": "[Oo]bj/",
            "description": "Lowercase 'obj/' directory matched by bracket pattern [Oo]bj/",
        },
        {
            "id": "obj-match-uppercase",
            "focus_pattern": "[Oo]bj/",
            "path": "Obj/intermediate.tmp",
            "is_space_path": False,
            "expected_ignored": True,
            "expected_pattern": "[Oo]bj/",
            "description": "Uppercase 'Obj/' directory matched by bracket pattern [Oo]bj/",
        },
        {
            "id": "obj-match-space-path",
            "focus_pattern": "[Oo]bj/",
            "path": "Custom Components/UI Library/obj/cache.dat",
            "is_space_path": True,
            "expected_ignored": True,
            "expected_pattern": "[Oo]bj/",
            "description": "Nested obj directory inside space-containing directory hierarchy",
        },
        {
            "id": "obj-nonmatch-actionscript-class",
            "focus_pattern": "[Oo]bj/",
            "path": "src/ObjectRenderer.as",
            "is_space_path": False,
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: legitimate ActionScript class file starting with Object remains visible",
        },
        {
            "id": "obj-nonmatch-file",
            "focus_pattern": "[Oo]bj/",
            "path": "obj.as",
            "is_space_path": False,
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: regular file 'obj.as' is not matched by directory rule [Oo]bj/",
        },
    ]


def main() -> None:
    force_fail = os.environ.get("R46_T026_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T026 Verification Check: Actionscript.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures (including space-containing paths & case variants)...")
    print("----------------------------------------------------------------------")

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="as-verify-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        case_env = detect_filesystem_case_sensitivity(tmp_repo)
        print(f"[*] Filesystem Case-Insensitive: {case_env['filesystem_case_insensitive']}")
        print(f"[*] Git core.ignorecase:         {case_env['git_core_ignorecase']}")
        print("----------------------------------------------------------------------")

        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install Actionscript .gitignore"], tmp_repo)

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

            if force_fail and tc["id"] == "bindebug-match-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<32} | Path: {rel_path:<45} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern}"
            )

            record = {
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": rel_path,
                "is_space_path": tc["is_space_path"],
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

        # Tracked file check
        tracked_rel = "bin-debug/tracked_compiler_config.xml"
        tracked_path = tmp_repo / tracked_rel
        tracked_path.parent.mkdir(parents=True, exist_ok=True)
        tracked_path.write_text("<config>initial</config>\n", encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], tmp_repo)
        run_command(["git", "commit", "-m", "Track pre-existing compiler config"], tmp_repo)

        tracked_path.write_text("<config>updated</config>\n", encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], tmp_repo)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print("----------------------------------------------------------------------")
        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain {tracked_rel}' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked compiler config modification was not reported by status")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T026",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "Actionscript.gitignore",
        "focus_patterns": ["bin-debug/", "bin-release/", "[Oo]bj/"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "case_and_filesystem_behavior": {
            "filesystem_case_insensitive": case_env["filesystem_case_insensitive"],
            "git_core_ignorecase": case_env["git_core_ignorecase"],
            "bracket_case_pattern_note": (
                "The pattern [Oo]bj/ explicitly handles case variants (obj/ and Obj/) at the pattern "
                "level using POSIX bracket expression [Oo], ensuring robust cross-platform matching regardless "
                "of whether the underlying filesystem or Git core.ignorecase is case-sensitive or case-insensitive."
            ),
        },
        "tracked_file_check": {
            "path": "bin-debug/tracked_compiler_config.xml",
            "description": "Pre-tracked compiler config inside ignored directory remains tracked and visible in status --porcelain",
            "porcelain_status": tracked_st_out,
            "passed": tracked_modified_visible,
        },
        "test_cases": actual_results,
        "summary": {
            "total_checks": len(fixtures) + 1,
            "passed": sum(1 for r in actual_results if r["passed"]) + (1 if tracked_modified_visible else 0),
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
        f"Platform: {tool_versions['platform']}\n"
        f"Filesystem case-insensitive: {case_env['filesystem_case_insensitive']}\n"
        f"Git core.ignorecase: {case_env['git_core_ignorecase']}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved tool versions to {TOOL_VERSIONS_FILE}")

    # Write run.log
    LOG_FILE.write_text(
        f"Command: python3 work/R46-T026/check.py\n"
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
    readme_content = f"""# Task R46-T026: Path and Case Assumptions in Actionscript.gitignore

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
  - Filesystem case-insensitive: `{case_env['filesystem_case_insensitive']}`
  - Git `core.ignorecase`: `{case_env['git_core_ignorecase']}`
- **Pattern Design**:
  - The pattern `[Oo]bj/` uses a POSIX character class `[Oo]` to explicitly match both lowercase `obj/` and titlecase `Obj/`.
  - This bracket expression ensures deterministic behavior across both case-sensitive platforms (Linux ext4) and case-insensitive platforms (macOS APFS / Windows NTFS).

---

## 3. Fixture Verification

### A. Focus Pattern: `bin-debug/`
- **Matching Fixtures**:
  - `bin-debug/app.swf`: Standard root output (`.gitignore:{pattern_lines.get('bin-debug/')}:bin-debug/`).
  - `Flash Games/Action Game/bin-debug/game.swf`: Nested inside space-containing directories.
- **Near-Miss Fixtures (Visible)**:
  - `bin-debug.as`: ActionScript source file (trailing slash prevents matching non-directories).

### B. Focus Pattern: `bin-release/`
- **Matching Fixtures**:
  - `bin-release/app.air`: Standard root release folder (`.gitignore:{pattern_lines.get('bin-release/')}:bin-release/`).
  - `Client Builds/Release Candidate/bin-release/app.air`: Nested inside space-containing directories.
- **Near-Miss Fixtures (Visible)**:
  - `bin-release_notes.txt`: Release notes text file.

### C. Focus Pattern: `[Oo]bj/`
- **Matching Fixtures**:
  - `obj/intermediate.tmp`: Lowercase folder (`.gitignore:{pattern_lines.get('[Oo]bj/')}:[Oo]bj/`).
  - `Obj/intermediate.tmp`: Uppercase folder (`.gitignore:{pattern_lines.get('[Oo]bj/')}:[Oo]bj/`).
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
