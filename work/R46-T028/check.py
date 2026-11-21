#!/usr/bin/env python3
"""
Verification check for R46-T028 (Issue #28):
Template: GWT.gitignore
Focus patterns: *.class, *.jar, *.war

Goal:
Create a reusable temporary-repository checker for this template;
verify both ignored artifacts and source files that must remain visible.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T028/evidence.json, run.log, and README.md.
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
TEMPLATE = REPO_ROOT / "GWT.gitignore"
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
        # --- Pattern 1: *.class ---
        {
            "id": "class-match-root",
            "focus_pattern": "*.class",
            "path": "App.class",
            "expected_ignored": True,
            "expected_pattern": "*.class",
            "description": "Compiled Java class byte-code at root",
        },
        {
            "id": "class-match-nested",
            "focus_pattern": "*.class",
            "path": "target/classes/com/example/MyModule.class",
            "expected_ignored": True,
            "expected_pattern": "*.class",
            "description": "Compiled class in nested directory hierarchy",
        },
        {
            "id": "class-nonmatch-source",
            "focus_pattern": "*.class",
            "path": "src/main/java/com/example/MyModule.java",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Legitimate Java source file MyModule.java must remain visible",
        },
        {
            "id": "class-nonmatch-classifier",
            "focus_pattern": "*.class",
            "path": "App.classifier",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: file ending with .classifier is not matched",
        },

        # --- Pattern 2: *.jar ---
        {
            "id": "jar-match-root",
            "focus_pattern": "*.jar",
            "path": "library.jar",
            "expected_ignored": True,
            "expected_pattern": "*.jar",
            "description": "Packaged JAR archive file",
        },
        {
            "id": "jar-match-nested",
            "focus_pattern": "*.jar",
            "path": "lib/gwt-user.jar",
            "expected_ignored": True,
            "expected_pattern": "*.jar",
            "description": "Nested GWT runtime library JAR",
        },
        {
            "id": "jar-nonmatch-pom",
            "focus_pattern": "*.jar",
            "path": "pom.xml",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Maven POM build file must remain visible",
        },
        {
            "id": "jar-nonmatch-sha1",
            "focus_pattern": "*.jar",
            "path": "lib/gwt-user.jar.sha1",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: checksum file ending with .sha1 remains visible",
        },

        # --- Pattern 3: *.war ---
        {
            "id": "war-match-root",
            "focus_pattern": "*.war",
            "path": "app.war",
            "expected_ignored": True,
            "expected_pattern": "*.war",
            "description": "Packaged web application archive",
        },
        {
            "id": "war-match-nested",
            "focus_pattern": "*.war",
            "path": "target/gwt-demo.war",
            "expected_ignored": True,
            "expected_pattern": "*.war",
            "description": "WAR package inside target build directory",
        },
        {
            "id": "war-nonmatch-webxml",
            "focus_pattern": "*.war",
            "path": "src/main/webapp/WEB-INF/web.xml",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Web deployment descriptor web.xml must remain visible",
        },
        {
            "id": "war-nonmatch-sig",
            "focus_pattern": "*.war",
            "path": "app.war.asc",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: digital signature file app.war.asc remains visible",
        },
    ]


def main() -> None:
    force_fail = os.environ.get("R46_T028_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T028 Verification Check: GWT.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures...")
    print("----------------------------------------------------------------------")

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="gwt-verify-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install GWT .gitignore"], tmp_repo)

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

            if force_fail and tc["id"] == "class-match-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<28} | Path: {rel_path:<40} | "
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
        tracked_rel = "src/main/webapp/WEB-INF/web.xml"
        tracked_path = tmp_repo / tracked_rel
        tracked_path.parent.mkdir(parents=True, exist_ok=True)
        tracked_path.write_text("<web-app>initial</web-app>\n", encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], tmp_repo)
        run_command(["git", "commit", "-m", "Track web.xml"], tmp_repo)

        tracked_path.write_text("<web-app>modified</web-app>\n", encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], tmp_repo)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print("----------------------------------------------------------------------")
        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain {tracked_rel}' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked web.xml modification was not reported by status")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T028",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "GWT.gitignore",
        "focus_patterns": ["*.class", "*.jar", "*.war"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "tracked_file_check": {
            "path": "src/main/webapp/WEB-INF/web.xml",
            "description": "Pre-tracked web deployment descriptor remains tracked and visible in status --porcelain",
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
        f"Command: python3 work/R46-T028/check.py\n"
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
    readme_content = f"""# Task R46-T028: Regression Checker for GWT.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T028` (Task 8 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #28](https://github.com/S-AI-Projects/gitignore/issues/28)
- **Template**: `GWT.gitignore`

---

## 1. Goal & Focus Patterns

Template: `GWT.gitignore`. Create a reusable temporary-repository checker for this template; verify both ignored artifacts and source files that must remain visible.

Focus patterns:
1. `*.class` (Compiled Java class byte-code)
2. `*.jar` (Java archive packages and dependencies)
3. `*.war` (Web application archive deployment packages)

---

## 2. Artifact vs. Source File Verification

In Google Web Toolkit (GWT) projects, compiled byte-code and packaged distribution archives are generated artifacts that must not be committed to version control, while Java source files (`*.java`), configuration files (`web.xml`), and Maven descriptors (`pom.xml`) must remain visible.

### A. Focus Pattern: `*.class`
- **Matching Fixtures**:
  - `App.class`: Root class file (`.gitignore:{pattern_lines.get('*.class')}:*.class`).
  - `target/classes/com/example/MyModule.class`: Nested class file.
- **Source Files (Must Remain Visible)**:
  - `src/main/java/com/example/MyModule.java`: Legitimate Java source code.
  - `App.classifier`: Near-miss filename.

### B. Focus Pattern: `*.jar`
- **Matching Fixtures**:
  - `library.jar`: Root archive file (`.gitignore:{pattern_lines.get('*.jar')}:*.jar`).
  - `lib/gwt-user.jar`: Nested GWT runtime library.
- **Source Files (Must Remain Visible)**:
  - `pom.xml`: Maven project build descriptor.
  - `lib/gwt-user.jar.sha1`: Checksum file.

### C. Focus Pattern: `*.war`
- **Matching Fixtures**:
  - `app.war`: Root web application package (`.gitignore:{pattern_lines.get('*.war')}:*.war`).
  - `target/gwt-demo.war`: Packaged target war.
- **Source Files (Must Remain Visible)**:
  - `src/main/webapp/WEB-INF/web.xml`: Web deployment descriptor.
  - `app.war.asc`: Detached signature file.

---

## 3. Tracked File Behavior

- Source configurations committed prior to applying ignore rules (e.g. `web.xml`) remain tracked.
- Modifying a pre-tracked configuration is reported as `M web.xml` by `git status --porcelain`.

---

## 4. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T028/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T028_FORCE_FAIL=1 python3 work/R46-T028/check.py
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
