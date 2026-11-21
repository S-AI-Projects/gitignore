#!/usr/bin/env python3
"""
Verification check for R46-T027 (Issue #27):
Template: Global/LibreOffice.gitignore
Focus pattern: .~lock.*#

Goal:
Connect the selected rule to the tool output it is intended to hide;
use official tool documentation and generated fixtures to distinguish
source files from lock files.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T027/evidence.json, run.log, and README.md.
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
TEMPLATE = REPO_ROOT / "Global" / "LibreOffice.gitignore"
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
        # --- Matching Lock File Fixtures (Ignored) ---
        {
            "id": "lock-match-odt-root",
            "focus_pattern": ".~lock.*#",
            "path": ".~lock.annual_report.odt#",
            "expected_ignored": True,
            "expected_pattern": ".~lock.*#",
            "description": "LibreOffice Writer lock file created during editing of annual_report.odt",
        },
        {
            "id": "lock-match-ods-nested",
            "focus_pattern": ".~lock.*#",
            "path": "financials/.~lock.budget_2026.ods#",
            "expected_ignored": True,
            "expected_pattern": ".~lock.*#",
            "description": "LibreOffice Calc lock file in nested financials directory",
        },
        {
            "id": "lock-match-odp-deep",
            "focus_pattern": ".~lock.*#",
            "path": "presentations/q4/.~lock.strategy.odp#",
            "expected_ignored": True,
            "expected_pattern": ".~lock.*#",
            "description": "LibreOffice Impress presentation lock file in subfolder",
        },

        # --- Legitimate Source Files (Must Remain Visible) ---
        {
            "id": "source-odt-visible",
            "focus_pattern": ".~lock.*#",
            "path": "annual_report.odt",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate LibreOffice Writer document must remain visible",
        },
        {
            "id": "source-ods-visible",
            "focus_pattern": ".~lock.*#",
            "path": "financials/budget_2026.ods",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate LibreOffice Calc spreadsheet must remain visible",
        },
        {
            "id": "source-odp-visible",
            "focus_pattern": ".~lock.*#",
            "path": "presentations/q4/strategy.odp",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate LibreOffice Impress presentation must remain visible",
        },

        # --- Near-Miss Fixtures (Remain Visible) ---
        {
            "id": "nearmiss-no-hash",
            "focus_pattern": ".~lock.*#",
            "path": ".~lock.document.odt",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: missing trailing hash '#' symbol remains visible",
        },
        {
            "id": "nearmiss-hash-only",
            "focus_pattern": ".~lock.*#",
            "path": "document.odt#",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: missing leading '.~lock.' prefix remains visible",
        },
        {
            "id": "nearmiss-regular-file-named-lock",
            "focus_pattern": ".~lock.*#",
            "path": "lock.odt",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: regular file named lock.odt is not matched by .~lock.*#",
        },
    ]


def main() -> None:
    force_fail = os.environ.get("R46_T027_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T027 Verification Check: Global/LibreOffice.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures...")
    print("----------------------------------------------------------------------")

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="libreoffice-verify-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install LibreOffice .gitignore"], tmp_repo)

        for tc in fixtures:
            rel_path = tc["path"]
            file_path = tmp_repo / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Create dummy payload simulating LibreOffice lock content
            file_path.write_text("user,host,timestamp,lockfile\n", encoding="utf-8")

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

            if force_fail and tc["id"] == "lock-match-odt-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<32} | Path: {rel_path:<36} | "
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

        # Tracked file check
        tracked_rel = "annual_report.odt"
        tracked_path = tmp_repo / tracked_rel
        tracked_path.write_text("initial document\n", encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], tmp_repo)
        run_command(["git", "commit", "-m", "Track initial document"], tmp_repo)

        tracked_path.write_text("edited document\n", encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], tmp_repo)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print("----------------------------------------------------------------------")
        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain {tracked_rel}' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked document modification was not reported by status")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T027",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "Global/LibreOffice.gitignore",
        "focus_patterns": [".~lock.*#"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "pattern_origin_analysis": {
            "origin": "LibreOffice Document Locking Protocol",
            "file_naming": ".~lock.<filename>#",
            "purpose": (
                "When a document (e.g. document.odt) is opened in LibreOffice, a lock file named "
                ".~lock.document.odt# is automatically created in the same directory. It stores the "
                "username, computer name, and lock timestamp to prevent concurrent write collisions. "
                "The rule .~lock.*# ensures these temporary locking artifacts are never committed, "
                "while safely preserving all real documents (*.odt, *.ods, *.odp)."
            ),
        },
        "tracked_file_check": {
            "path": "annual_report.odt",
            "description": "Pre-tracked LibreOffice document remains tracked and visible in status --porcelain",
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
        f"Platform: {tool_versions['platform']}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved tool versions to {TOOL_VERSIONS_FILE}")

    # Write run.log
    LOG_FILE.write_text(
        f"Command: python3 work/R46-T027/check.py\n"
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
    readme_content = f"""# Task R46-T027: Pattern Origin in Global/LibreOffice.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T027` (Task 7 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #27](https://github.com/S-AI-Projects/gitignore/issues/27)
- **Template**: `Global/LibreOffice.gitignore`

---

## 1. Goal & Focus Pattern

Template: `Global/LibreOffice.gitignore`. Connect the selected rule to the tool output it is intended to hide; distinguish source files from lock output.

Focus pattern:
- `.~lock.*#` (LibreOffice active document session lock file)

---

## 2. Pattern Origin & Tool Behavior

1. **Origin in LibreOffice**:
   - When an office document (such as `report.odt`, `budget.ods`, or `slides.odp`) is opened for editing, LibreOffice creates a small lock file in the same directory following the exact convention `.~lock.<filename>#`.
   - The file contains single-line CSV metadata (`user,computer,date,url`) to inform other instances that the file is in use.
   - Upon a normal application close, LibreOffice deletes this file. However, if LibreOffice terminates unexpectedly or remains open during a commit, the lock file persists on disk.

2. **Rule Precision**:
   - The pattern `.~lock.*#` requires:
     - Prefix: `.~lock.`
     - Wildcard body: `*`
     - Suffix: `#`
   - This exact shape cleanly matches all lock files while preventing false positives against actual documents (`report.odt`, `budget.ods`) and near-misses.

---

## 3. Fixture Verification

### A. Matching Lock Files (Ignored)
- `.~lock.annual_report.odt#`: Root Writer lock file (`.gitignore:{pattern_lines.get('.~lock.*#')}:.~lock.*#`).
- `financials/.~lock.budget_2026.ods#`: Nested Calc spreadsheet lock file.
- `presentations/q4/.~lock.strategy.odp#`: Nested Impress presentation lock file.

### B. Legitimate Source Files (Must Remain Visible)
- `annual_report.odt`: Legitimate Writer document.
- `financials/budget_2026.ods`: Legitimate Calc spreadsheet.
- `presentations/q4/strategy.odp`: Legitimate Impress presentation.

### C. Near-Miss Fixtures (Visible)
- `.~lock.document.odt`: Missing trailing `#`.
- `document.odt#`: Missing leading `.~lock.` prefix.
- `lock.odt`: Regular file named `lock.odt`.

---

## 4. Tracked File Behavior

- Source documents tracked prior to applying ignore rules (e.g. `annual_report.odt`) remain tracked.
- Modifying a pre-tracked document is reported as `M annual_report.odt` by `git status --porcelain`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T027/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T027_FORCE_FAIL=1 python3 work/R46-T027/check.py
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
