#!/usr/bin/env python3
"""
Verification check for R46-T022 (Issue #22):
Template: Global/CodeKit.gitignore
Focus patterns: config.codekit, config.codekit3, /min

Goal:
Place equivalent filenames at the repository root and two nested directories;
show which rules are anchored and which apply anywhere.

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T022/evidence.json, run.log, and README.md.
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
TEMPLATE = REPO_ROOT / "Global" / "CodeKit.gitignore"
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
        # ====================================================================
        # Focus Pattern 1: config.codekit (Unanchored - matches everywhere)
        # ====================================================================
        {
            "id": "codekit-root-match",
            "focus_pattern": "config.codekit",
            "path": "config.codekit",
            "depth": "root",
            "expected_ignored": True,
            "expected_pattern": "config.codekit",
            "description": "Unanchored pattern matches config.codekit at repository root",
        },
        {
            "id": "codekit-level1-match",
            "focus_pattern": "config.codekit",
            "path": "theme/config.codekit",
            "depth": "nested_level_1",
            "expected_ignored": True,
            "expected_pattern": "config.codekit",
            "description": "Unanchored pattern matches config.codekit in level 1 nested directory",
        },
        {
            "id": "codekit-level2-match",
            "focus_pattern": "config.codekit",
            "path": "theme/assets/config.codekit",
            "depth": "nested_level_2",
            "expected_ignored": True,
            "expected_pattern": "config.codekit",
            "description": "Unanchored pattern matches config.codekit in level 2 deeply nested directory",
        },
        {
            "id": "codekit-nonmatch-bak",
            "focus_pattern": "config.codekit",
            "path": "config.codekit.bak",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: backup file (.bak). Remains visible because pattern requires exact name",
        },
        {
            "id": "codekit-nonmatch-dist",
            "focus_pattern": "config.codekit",
            "path": "theme/config.codekit.dist",
            "depth": "nested_level_1",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: distribution template (.dist). Must remain tracked in version control",
        },
        {
            "id": "codekit-nonmatch-prefix",
            "focus_pattern": "config.codekit",
            "path": "my_config.codekit",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: custom prefixed filename. Remains visible because pattern has no wildcard",
        },

        # ====================================================================
        # Focus Pattern 2: config.codekit3 (Unanchored - matches everywhere)
        # ====================================================================
        {
            "id": "codekit3-root-match",
            "focus_pattern": "config.codekit3",
            "path": "config.codekit3",
            "depth": "root",
            "expected_ignored": True,
            "expected_pattern": "config.codekit3",
            "description": "Unanchored pattern matches config.codekit3 at repository root",
        },
        {
            "id": "codekit3-level1-match",
            "focus_pattern": "config.codekit3",
            "path": "app/config.codekit3",
            "depth": "nested_level_1",
            "expected_ignored": True,
            "expected_pattern": "config.codekit3",
            "description": "Unanchored pattern matches config.codekit3 in level 1 nested directory",
        },
        {
            "id": "codekit3-level2-match",
            "focus_pattern": "config.codekit3",
            "path": "app/frontend/config.codekit3",
            "depth": "nested_level_2",
            "expected_ignored": True,
            "expected_pattern": "config.codekit3",
            "description": "Unanchored pattern matches config.codekit3 in level 2 deeply nested directory",
        },
        {
            "id": "codekit3-nonmatch-sample",
            "focus_pattern": "config.codekit3",
            "path": "config.codekit3.sample",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: sample configuration file. Must remain tracked for collaborators",
        },
        {
            "id": "codekit3-nonmatch-version",
            "focus_pattern": "config.codekit3",
            "path": "app/config.codekit2",
            "depth": "nested_level_1",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: legacy version filename config.codekit2 is not matched",
        },
        {
            "id": "codekit3-nonmatch-prefix",
            "focus_pattern": "config.codekit3",
            "path": "theme/custom-config.codekit3",
            "depth": "nested_level_1",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: prefixed custom config file remains visible",
        },

        # ====================================================================
        # Focus Pattern 3: /min (Root-Anchored - matches ONLY at repository root)
        # ====================================================================
        {
            "id": "min-root-dir-match",
            "focus_pattern": "/min",
            "path": "min/app.js",
            "depth": "root",
            "expected_ignored": True,
            "expected_pattern": "/min",
            "description": "Anchored pattern /min matches minified assets inside root /min directory",
        },
        {
            "id": "min-root-css-match",
            "focus_pattern": "/min",
            "path": "min/styles.css",
            "depth": "root",
            "expected_ignored": True,
            "expected_pattern": "/min",
            "description": "Anchored pattern /min matches stylesheet inside root /min directory",
        },
        {
            "id": "min-level1-nested-visible",
            "focus_pattern": "/min",
            "path": "assets/min/app.js",
            "depth": "nested_level_1",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "CRUCIAL: Level 1 nested assets/min/ is NOT ignored because /min is anchored to root",
        },
        {
            "id": "min-level2-nested-visible",
            "focus_pattern": "/min",
            "path": "app/static/min/bundle.css",
            "depth": "nested_level_2",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "CRUCIAL: Level 2 nested app/static/min/ is NOT ignored because /min is anchored to root",
        },
        {
            "id": "min-nonmatch-minute",
            "focus_pattern": "/min",
            "path": "minute.txt",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: prefix match 'minute.txt' is not matched by exact name '/min'",
        },
        {
            "id": "min-nonmatch-minimal",
            "focus_pattern": "/min",
            "path": "minimal/bundle.js",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: directory 'minimal/' is not matched by exact name '/min'",
        },
        {
            "id": "min-nonmatch-minjs",
            "focus_pattern": "/min",
            "path": "min.js",
            "depth": "root",
            "expected_ignored": False,
            "expected_pattern": None,
            "description": "Near-miss: regular file 'min.js' is distinct from directory '/min'",
        },
    ]


def main() -> None:
    force_fail = os.environ.get("R46_T022_FORCE_FAIL") == "1"

    if not TEMPLATE.is_file():
        print(f"Error: Template not found at {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE.read_text(encoding="utf-8")
    pattern_lines = get_template_pattern_lines(template_text)
    tool_versions = get_tool_versions()
    fixtures = define_fixtures()

    print("======================================================================")
    print(" R46-T022 Verification Check: Global/CodeKit.gitignore")
    print("======================================================================")
    print(f"Template path: {TEMPLATE}")
    print(f"Git version:   {tool_versions['git']}")
    print(f"Python:        {tool_versions['python']}")
    print(f"Platform:      {tool_versions['platform']}")
    print(f"Testing {len(fixtures)} fixtures across root, level 1, and level 2...")
    print("----------------------------------------------------------------------")

    actual_results = []
    failures = []

    with tempfile.TemporaryDirectory(prefix="codekit-verify-") as tmpdir:
        tmp_repo = Path(tmpdir)
        run_command(["git", "init"], tmp_repo)
        run_command(["git", "config", "user.name", "Check Runner"], tmp_repo)
        run_command(["git", "config", "user.email", "checker@example.invalid"], tmp_repo)

        # 1. Install .gitignore template
        (tmp_repo / ".gitignore").write_text(template_text, encoding="utf-8")
        run_command(["git", "add", ".gitignore"], tmp_repo)
        run_command(["git", "commit", "-m", "Install CodeKit .gitignore"], tmp_repo)

        # 2. Test each fixture
        for tc in fixtures:
            rel_path = tc["path"]
            file_path = tmp_repo / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file
            file_path.write_text(f"content for {rel_path}\n", encoding="utf-8")

            # Run git check-ignore -v --no-index
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

            # Run git status --porcelain
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

            if force_fail and tc["id"] == "codekit-root-match":
                passed = False

            status_str = "PASS" if passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<28} | Depth: {tc['depth']:<15} | "
                f"Path: {rel_path:<32} | "
                f"Ignored: {actual_ignored} (exp: {tc['expected_ignored']}) | "
                f"Pattern: {actual_pattern}"
            )

            record = {
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": rel_path,
                "depth": tc["depth"],
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
                failures.append(
                    f"{tc['id']} ({rel_path}): expected ignored={tc['expected_ignored']} "
                    f"pattern={tc['expected_pattern']}, got ignored={actual_ignored} pattern={actual_pattern}"
                )

            # Clean up fixture
            if file_path.exists():
                file_path.unlink()

        # 3. Tracked file behavior verification
        tracked_rel = "config.codekit"
        tracked_path = tmp_repo / tracked_rel
        tracked_path.write_text('{"project": "initial"}\n', encoding="utf-8")
        run_command(["git", "add", "-f", tracked_rel], tmp_repo)
        run_command(["git", "commit", "-m", "Track pre-existing config.codekit"], tmp_repo)

        # Modify tracked file
        tracked_path.write_text('{"project": "modified"}\n', encoding="utf-8")
        _, tracked_st_out, _ = run_command(["git", "status", "--porcelain", tracked_rel], tmp_repo)
        tracked_modified_visible = f"M {tracked_rel}" in tracked_st_out or f" M {tracked_rel}" in tracked_st_out

        print("----------------------------------------------------------------------")
        print(f"[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: 'git status --porcelain config.codekit' -> '{tracked_st_out}'")
        if not tracked_modified_visible:
            failures.append("Tracked config.codekit modification was not reported by git status --porcelain")

    # Structure evidence payload
    all_passed = len(failures) == 0 and tracked_modified_visible
    evidence = {
        "task_id": "R46-T022",
        "student": "sumit kavishwar",
        "urn": "E26B07F0687",
        "template": "Global/CodeKit.gitignore",
        "focus_patterns": ["config.codekit", "config.codekit3", "/min"],
        "tool_versions": tool_versions,
        "pattern_lines": pattern_lines,
        "nested_matching_analysis": {
            "unanchored_rules": {
                "patterns": ["config.codekit", "config.codekit3"],
                "behavior": "No leading slash. Matches at project root, Level 1 nested, and Level 2 nested directories.",
            },
            "root_anchored_rules": {
                "patterns": ["/min"],
                "behavior": "Leading slash anchors pattern strictly to repository root. Subdirectory matches (assets/min/, app/static/min/) are NOT ignored and remain visible.",
            },
        },
        "tracked_file_check": {
            "path": "config.codekit",
            "description": "Pre-tracked config.codekit modification remains tracked and visible in status --porcelain",
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
        f"Command: python3 work/R46-T022/check.py\n"
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
    readme_content = f"""# Task R46-T022: Nested Path Matching in Global/CodeKit.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T022` (Task 2 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #22](https://github.com/S-AI-Projects/gitignore/issues/22)
- **Template**: `Global/CodeKit.gitignore`

---

## 1. Goal & Focus Patterns

Template: `Global/CodeKit.gitignore`. Place equivalent filenames at the repository root and two nested directories; demonstrate which rules are anchored and which apply anywhere:

1. `config.codekit` (Unanchored - CodeKit 2 project configuration)
2. `config.codekit3` (Unanchored - CodeKit 3 project configuration)
3. `/min` (Root-Anchored - CodeKit default minified build output directory)

---

## 2. Path Anchoring Analysis

### A. Unanchored Patterns: `config.codekit` & `config.codekit3`
- **Rule Syntax**: `config.codekit` and `config.codekit3` do not have a leading slash (`/`).
- **Gitignore Behavior**: A pattern without a slash matches against the basename in **any directory** throughout the entire project hierarchy.
- **Verification Across Three Depths**:
  - **Root**: `config.codekit` $\\rightarrow$ **IGNORED** (matches `.gitignore:{pattern_lines.get('config.codekit')}:config.codekit`)
  - **Level 1 Nested**: `theme/config.codekit` $\\rightarrow$ **IGNORED** (matches `.gitignore:{pattern_lines.get('config.codekit')}:config.codekit`)
  - **Level 2 Nested**: `theme/assets/config.codekit` $\\rightarrow$ **IGNORED** (matches `.gitignore:{pattern_lines.get('config.codekit')}:config.codekit`)
- **Near-Miss Names**:
  - `config.codekit.bak` (backup file) remains **VISIBLE** (exit code 1).
  - `config.codekit.dist` (sample distribution file) remains **VISIBLE** to allow version-controlled project templates.
  - `my_config.codekit` (prefixed custom file) remains **VISIBLE**.

### B. Root-Anchored Pattern: `/min`
- **Rule Syntax**: The pattern begins with a leading forward slash `/`.
- **Gitignore Behavior**: A leading slash anchors the match strictly to the directory where the `.gitignore` file resides (the repository root). It matches `/min/` at the root, but **does not match** `min` directories located within subdirectories.
- **Verification Across Three Depths**:
  - **Root**: `min/app.js` $\\rightarrow$ **IGNORED** (matches `.gitignore:{pattern_lines.get('/min')}:/min`)
  - **Level 1 Nested**: `assets/min/app.js` $\\rightarrow$ **VISIBLE** (exit code 1; does not match `/min`)
  - **Level 2 Nested**: `app/static/min/bundle.css` $\\rightarrow$ **VISIBLE** (exit code 1; does not match `/min`)
- **Near-Miss Names**:
  - `minute.txt`: Distinct file starting with 'min' remains **VISIBLE**.
  - `minimal/bundle.js`: Distinct folder starting with 'min' remains **VISIBLE**.
  - `min.js`: Individual minified file named 'min.js' remains **VISIBLE**.

---

## 3. Tracked File Behavior

- Files committed before installing ignore rules (e.g., pre-tracked `config.codekit`) remain tracked by Git.
- Modifying a pre-tracked file is correctly reported by `git status --porcelain` as `M config.codekit`.

---

## 4. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T022/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T022_FORCE_FAIL=1 python3 work/R46-T022/check.py
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
