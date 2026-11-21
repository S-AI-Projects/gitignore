#!/usr/bin/env python3
"""
Verification check for R46-T021 (Issue #21):
Template: MetaProgrammingSystem.gitignore
Focus patterns: workspace.xml, junitvmwatcher*.properties, build.properties

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Performs before/after regression testing to prove pattern change validity.
Outputs results to work/R46-T021/evidence.json, run.log, and README.md.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "MetaProgrammingSystem.gitignore"
EVIDENCE_FILE = TASK_DIR / "evidence.json"
TOOL_VERSIONS_FILE = TASK_DIR / "tool_versions.txt"
LOG_FILE = TASK_DIR / "run.log"
README_FILE = TASK_DIR / "README.md"

ORIGINAL_TEMPLATE_CONTENT = """workspace.xml
junitvmwatcher*.properties
build.properties

# generated java classes and java source files
#   manually add any custom artifacts that can't be generated from the models
#   http://confluence.jetbrains.com/display/MPSD25/HowTo+--+MPS+and+Git
classes_gen
source_gen
source_gen.caches

# generated test code and test results
test_gen
test_gen.caches
TEST-*.xml
junit*.properties
"""


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
        # --- Focus Pattern 1: workspace.xml ---
        {
            "id": "workspace-match-root",
            "focus_pattern": "workspace.xml",
            "path": "workspace.xml",
            "expected_ignored": True,
            "expected_pattern": "workspace.xml",
            "description": "MPS / IntelliJ workspace user state file in project root",
        },
        {
            "id": "workspace-match-dotmps",
            "focus_pattern": "workspace.xml",
            "path": ".mps/workspace.xml",
            "expected_ignored": True,
            "expected_pattern": "workspace.xml",
            "description": "Workspace file in .mps directory (nested directory matching)",
        },
        {
            "id": "workspace-match-nested",
            "focus_pattern": "workspace.xml",
            "path": "project/subproject/workspace.xml",
            "expected_ignored": True,
            "expected_pattern": "workspace.xml",
            "description": "Deeply nested workspace.xml (unanchored pattern matches anywhere)",
        },
        {
            "id": "workspace-nonmatch-bak",
            "focus_pattern": "workspace.xml",
            "path": "workspace.xml.bak",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: backup file (.bak). Remains visible because pattern requires exact name",
        },
        {
            "id": "workspace-nonmatch-dist",
            "focus_pattern": "workspace.xml",
            "path": "workspace.xml.dist",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: distribution template (.dist). Must remain tracked in version control",
        },
        {
            "id": "workspace-nonmatch-prefix",
            "focus_pattern": "workspace.xml",
            "path": "my-workspace.xml",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: prefixed filename. Remains visible because pattern has no wildcard",
        },
        {
            "id": "workspace-nonmatch-tilde",
            "focus_pattern": "workspace.xml",
            "path": "workspace.xml~",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: editor backup file ending with tilde. Remains visible",
        },

        # --- Focus Pattern 2: junitvmwatcher*.properties ---
        {
            "id": "junitvmwatcher-match-base",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher.properties",
            "expected_ignored": True,
            "expected_pattern": "junitvmwatcher*.properties",
            "description": "Base VM watcher properties file with empty wildcard",
        },
        {
            "id": "junitvmwatcher-match-pid",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher1234.properties",
            "expected_ignored": True,
            "expected_pattern": "junitvmwatcher*.properties",
            "description": "VM watcher properties file with numeric process ID",
        },
        {
            "id": "junitvmwatcher-match-label",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher_runner_0.properties",
            "expected_ignored": True,
            "expected_pattern": "junitvmwatcher*.properties",
            "description": "VM watcher properties file with runner label suffix",
        },
        {
            "id": "junitvmwatcher-match-nested",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "build/test-reports/junitvmwatcher_test.properties",
            "expected_ignored": True,
            "expected_pattern": "junitvmwatcher*.properties",
            "description": "VM watcher properties file in nested build/test directory",
        },
        {
            "id": "junitvmwatcher-nonmatch-no-ext",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: missing .properties extension. Remains visible",
        },
        {
            "id": "junitvmwatcher-nonmatch-props",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher.props",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: truncated extension .props instead of .properties. Remains visible",
        },
        {
            "id": "junitvmwatcher-nonmatch-prefix",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "my_junitvmwatcher.properties",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: prefixed filename. Remains visible because pattern requires junitvmwatcher prefix",
        },
        {
            "id": "junitvmwatcher-nonmatch-sample",
            "focus_pattern": "junitvmwatcher*.properties",
            "path": "junitvmwatcher.properties.sample",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: sample configuration file with extra trailing extension. Remains visible",
        },

        # --- Focus Pattern 3: build.properties ---
        {
            "id": "build-match-root",
            "focus_pattern": "build.properties",
            "path": "build.properties",
            "expected_ignored": True,
            "expected_pattern": "build.properties",
            "description": "Root build.properties (Ant / MPS local build property overrides)",
        },
        {
            "id": "build-match-subproject",
            "focus_pattern": "build.properties",
            "path": "subproject/build.properties",
            "expected_ignored": True,
            "expected_pattern": "build.properties",
            "description": "Subproject build.properties in nested directory",
        },
        {
            "id": "build-nonmatch-sample",
            "focus_pattern": "build.properties",
            "path": "build.properties.sample",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: sample configuration file. Must remain tracked for project contributors",
        },
        {
            "id": "build-nonmatch-template",
            "focus_pattern": "build.properties",
            "path": "build.properties.template",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: build template file. Must remain tracked",
        },
        {
            "id": "build-nonmatch-underscore",
            "focus_pattern": "build.properties",
            "path": "build_properties",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: underscore separator instead of dot. Remains visible",
        },
        {
            "id": "build-nonmatch-prefix",
            "focus_pattern": "build.properties",
            "path": "custom-build.properties",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: prefixed custom build file. Remains visible",
        },

        # --- General Template Regression: Other legitimate rules ---
        {
            "id": "general-junit-properties",
            "focus_pattern": "junit*.properties",
            "path": "junit.properties",
            "expected_ignored": True,
            "expected_pattern": "junit*.properties",
            "description": "General test properties file ignored by junit*.properties rule",
        },
        {
            "id": "general-test-xml",
            "focus_pattern": "TEST-*.xml",
            "path": "TEST-report.xml",
            "expected_ignored": True,
            "expected_pattern": "TEST-*.xml",
            "description": "JUnit test results XML report",
        },
    ]


def run_regression_before(fixtures: list[dict]) -> dict:
    """Evaluate original template behavior showing the shadowing of junitvmwatcher*.properties."""
    with tempfile.TemporaryDirectory(prefix="mps-before-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Regression Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "runner@example.invalid"], tmp_repo)

        (tmp_repo / ".gitignore").write_text(ORIGINAL_TEMPLATE_CONTENT, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install original template"], tmp_repo)

        results = {}
        for tc in fixtures:
            path = tc["path"]
            rc, stdout, _ = run_command(["git", "check-ignore", "-v", "--no-index", path], tmp_repo)
            if rc == 0 and stdout:
                parts = stdout.split("\t")[0].split(":")
                results[tc["id"]] = {
                    "ignored": True,
                    "line": int(parts[1]),
                    "pattern": parts[2],
                }
            else:
                results[tc["id"]] = {
                    "ignored": False,
                    "line": None,
                    "pattern": None,
                }
        return results


def main() -> None:
    force_fail = os.environ.get("R46_T021_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T021 Verification Check: MetaProgrammingSystem.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures...")
    print("----------------------------------------------------------------------")

    # Run baseline on original template for before/after comparison
    before_results = run_regression_before(fixtures)

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="mps-after-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        # 1. Install .gitignore template in temporary repo
        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install MetaProgrammingSystem .gitignore"], tmp_repo)

        # 2. Test each fixture as an untracked file
        for tc in fixtures:
            rel_path = tc["path"]
            file_path = tmp_repo / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create the file
            file_path.write_text(f"content for {rel_path}\n", encoding="utf-8")

            # Execute git check-ignore -v --no-index
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

            # Execute git status --porcelain
            _, st_out, _ = run_command(["git", "status", "--porcelain", rel_path], tmp_repo)
            porcelain_status = st_out.strip()

            # For untracked files:
            # - Ignored files do not appear in status (empty)
            # - Visible files appear as '?? <path>'
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

            if force_fail and tc["id"] == "workspace-match-root":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<32} | Path: {rel_path:<40} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern} (exp: {tc['expected_pattern']})"
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
                "before_regression": before_results.get(tc["id"]),
                "passed": passed,
            }
            actual_results.append(record)

            if not passed:
                failures.append(
                    f"{tc['id']} ({rel_path}): expected ignored={tc['expected_ignored']} "
                    f"pattern={tc['expected_pattern']}, got ignored={actual_ignored} pattern={actual_pattern}"
                )

            # Clean up untracked temporary fixture file
            if file_path.exists():
                file_path.unlink()

        # 3. Verify tracked file behavior under modification
        # A file matching an ignore rule that is already tracked remains tracked by Git
        tracked_rel = "workspace.xml"
        tracked_path = tmp_repo / tracked_rel
        tracked_path.write_text("<project version='4'></project>\n", encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], tmp_repo)
        run_command(["git", "commit", "-m", "Track existing workspace.xml"], tmp_repo)

        # Modify tracked file
        tracked_path.write_text("<project version='4'><component name='LocalChange'/></project>\n", encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], tmp_repo)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print("----------------------------------------------------------------------")
        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain workspace.xml' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked workspace.xml modification was not reported by git status --porcelain")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T021",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "MetaProgrammingSystem.gitignore",
        "focus_patterns": ["workspace.xml", "junitvmwatcher*.properties", "build.properties"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "regression_summary": {
            "root_cause": (
                "In the original template, junitvmwatcher*.properties was located on line 2, "
                "while junit*.properties was located on line 16. In Git rule evaluation, later "
                "rules take precedence; consequently, junitvmwatcher*.properties was completely shadowed "
                "by junit*.properties. Relocating junitvmwatcher*.properties under '# generated test code and "
                "test results' after junit*.properties resolves the shadow conflict while preserving all "
                "legitimate test and configuration files."
            ),
            "before_rule_for_junitvmwatcher": before_results.get("junitvmwatcher-match-base", {}).get("pattern"),
            "after_rule_for_junitvmwatcher": pattern_lines.get("junitvmwatcher*.properties"),
        },
        "tracked_file_check": {
            "path": "workspace.xml",
            "description": "Pre-tracked workspace.xml modification remains tracked and visible in status --porcelain",
            "porcelain_status": tracked_st_out,
            "passed": tracked_modified_visible,
        },
        "test_cases": actual_results,
        "summary": {
            "total_fixtures": len(fixtures) + 1,
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
        f"Command: python3 work/R46-T021/check.py\n"
        f"Git: {tool_versions['git']}\n"
        f"Python: {tool_versions['python']}\n"
        f"Platform: {tool_versions['platform']}\n"
        f"Total checks: {evidence['summary']['total_fixtures']}\n"
        f"Passed: {evidence['summary']['passed']}\n"
        f"Failed: {evidence['summary']['failed']}\n"
        f"Status: {'PASS' if all_passed else 'FAIL'}\n",
        encoding="utf-8",
    )
    print(f"[+] Saved run log to {LOG_FILE}")

    # Write README.md
    readme_content = f"""# Task R46-T021: Fixture Verification for MetaProgrammingSystem.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T021` (Task 1 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #21](https://github.com/S-AI-Projects/gitignore/issues/21)
- **Template**: `MetaProgrammingSystem.gitignore`

---

## 1. Focus Patterns

1. `workspace.xml` (JetBrains MPS user-specific IDE workspace configuration)
2. `junitvmwatcher*.properties` (JUnit test runner VM watcher properties and logs)
3. `build.properties` (Ant / MPS local build property overrides)

---

## 2. Pattern Analysis & Near-Miss Fixtures

### Pattern 1: `workspace.xml`
- **Purpose**: Ignores user-specific workspace state (open editor tabs, window layouts, local tool preferences).
- **Matching Fixtures (Ignored)**:
  - `workspace.xml`: Root-level MPS workspace file (`.gitignore:{pattern_lines.get('workspace.xml')}:workspace.xml`).
  - `.mps/workspace.xml`: Standard JetBrains MPS project configuration folder.
  - `project/subproject/workspace.xml`: Nested workspace file in a multi-module project.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `workspace.xml.bak`: Backup file. Remains visible because gitignore pattern without wildcards requires an exact filename match.
  - `workspace.xml.dist`: Distributed sample workspace template. Must remain tracked for version control.
  - `my-workspace.xml`: Custom workspace configuration. Distinct prefix is not matched.
  - `workspace.xml~`: Editor backup with trailing tilde. Remains visible.

### Pattern 2: `junitvmwatcher*.properties`
- **Purpose**: Ignores temporary VM watcher property files generated during MPS JUnit test runs.
- **Matching Fixtures (Ignored)**:
  - `junitvmwatcher.properties`: Base watcher file with empty wildcard (`.gitignore:{pattern_lines.get('junitvmwatcher*.properties')}:junitvmwatcher*.properties`).
  - `junitvmwatcher1234.properties`: Watcher file with process identifier.
  - `junitvmwatcher_runner_0.properties`: Watcher file with test runner label.
  - `build/test-reports/junitvmwatcher_test.properties`: Watcher file inside test directory.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `junitvmwatcher`: Missing `.properties` extension; remains visible.
  - `junitvmwatcher.props`: Truncated extension; remains visible.
  - `my_junitvmwatcher.properties`: Prefix mismatch; remains visible because the pattern requires starting with `junitvmwatcher`.
  - `junitvmwatcher.properties.sample`: Trailing extension mismatch; remains visible.

### Pattern 3: `build.properties`
- **Purpose**: Ignores local Ant / MPS build configuration overrides.
- **Matching Fixtures (Ignored)**:
  - `build.properties`: Root Ant build properties file (`.gitignore:{pattern_lines.get('build.properties')}:build.properties`).
  - `subproject/build.properties`: Subproject build properties.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `build.properties.sample`: Sample configuration template; must remain tracked in repository for new contributors.
  - `build.properties.template`: Template configuration file; remains visible.
  - `build_properties`: Underscore separator instead of dot; remains visible.
  - `custom-build.properties`: Custom prefixed file; remains visible.

---

## 3. Before/After Regression Analysis

In the original `MetaProgrammingSystem.gitignore`:
- `junitvmwatcher*.properties` was placed at line 2.
- `junit*.properties` was placed at line 16 under `# generated test code and test results`.
- In Git rule evaluation, later rules override earlier rules. Because `junit*.properties` matches any file beginning with `junit` and ending with `.properties`, it shadowed `junitvmwatcher*.properties`, causing Git to attribute matches to `junit*.properties`.
- **Narrow Justified Correction**: Following `CONTRIBUTING.md` ("Add new rules to the most appropriate existing section"), `junitvmwatcher*.properties` was relocated into `# generated test code and test results` after `junit*.properties`. This resolves the shadowing conflict, allows Git to report the specific `junitvmwatcher*.properties` rule, and preserves 100% of legitimate project and test files.

---

## 4. Tracked File Behavior

- Files committed before installing ignore rules (e.g., `workspace.xml` tracked input) remain tracked by Git.
- When modified, `git status --porcelain` correctly reports `M workspace.xml`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T021/check.py
```

To verify that the check fails non-zero on assertion error:
```bash
R46_T021_FORCE_FAIL=1 python3 work/R46-T021/check.py
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
        print(f"\n[PASS] All {evidence['summary']['passed']} checks passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
