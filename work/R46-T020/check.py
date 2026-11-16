#!/usr/bin/env python3
"""
Verification check for R46-T020 (Issue #20):
Template: Phalcon.gitignore
Focus patterns: /cache/, /config/development/

Documents a realistic Phalcon project tree that uses this template:
- Marks ignored outputs and tracked inputs with the matching rule and line number.
- Verifies positive ignored outputs (compiled volt views, local dev overrides).
- Verifies tracked inputs (MVC sources, production configs, public assets).
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T020/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Phalcon.gitignore")
EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), "evidence.json")


def run_command(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def get_git_version():
    res = subprocess.run(["git", "--version"], capture_output=True, text=True)
    return res.stdout.strip()


def check_ignore(cwd, filepath):
    cmd = ["git", "check-ignore", "-v", "--no-index", filepath]
    ret, stdout, stderr = run_command(cmd, cwd)
    if ret == 0:
        raw = stdout.strip()
        parts = raw.split("\t", 1)
        rule_info = parts[0]
        subparts = rule_info.split(":", 2)
        line_num = int(subparts[1]) if len(subparts) >= 2 and subparts[1].isdigit() else None
        pattern = subparts[2] if len(subparts) >= 3 else None
        return {
            "ignored": True,
            "pattern": pattern,
            "rule_line": line_num,
            "raw_output": raw,
            "returncode": ret,
        }
    else:
        return {
            "ignored": False,
            "pattern": None,
            "rule_line": None,
            "raw_output": stdout.strip(),
            "returncode": ret,
        }


def main():
    force_fail = os.environ.get("R46_T020_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t020_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Ignored outputs
            {
                "id": "cache-volt-output",
                "focus_pattern": "/cache/",
                "path": "cache/volt/compiled_view.php",
                "role": "ignored_output",
                "description": "Compiled Volt template in root /cache/ is ignored",
                "expected": {"ignored": True, "pattern": "/cache/", "rule_line": 2},
            },
            {
                "id": "cache-data-output",
                "focus_pattern": "/cache/",
                "path": "cache/data/models_metadata.php",
                "role": "ignored_output",
                "description": "Phalcon ORM metadata cache in root /cache/ is ignored",
                "expected": {"ignored": True, "pattern": "/cache/", "rule_line": 2},
            },
            {
                "id": "config-dev-json-output",
                "focus_pattern": "/config/development/",
                "path": "config/development/config.json",
                "role": "ignored_output",
                "description": "Local dev configuration override in /config/development/ is ignored",
                "expected": {"ignored": True, "pattern": "/config/development/", "rule_line": 4},
            },
            {
                "id": "config-dev-db-output",
                "focus_pattern": "/config/development/",
                "path": "config/development/database.php",
                "role": "ignored_output",
                "description": "Local dev database credentials in /config/development/ is ignored",
                "expected": {"ignored": True, "pattern": "/config/development/", "rule_line": 4},
            },
            # Tracked inputs & nonmatching fixtures
            {
                "id": "app-controller-input",
                "focus_pattern": "/cache/",
                "path": "app/controllers/IndexController.php",
                "role": "tracked_input",
                "description": "Application controller source code must remain visible and tracked",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "app-view-input",
                "focus_pattern": "/cache/",
                "path": "app/views/index.volt",
                "role": "tracked_input",
                "description": "Application view template source must remain visible and tracked",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "config-base-input",
                "focus_pattern": "/config/development/",
                "path": "config/config.php",
                "role": "tracked_input",
                "description": "Base framework configuration must remain visible and tracked",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "config-production-input",
                "focus_pattern": "/config/development/",
                "path": "config/production/config.json",
                "role": "tracked_input",
                "description": "Production baseline config must remain visible and tracked",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "public-index-input",
                "focus_pattern": "/cache/",
                "path": "public/index.php",
                "role": "tracked_input",
                "description": "Public front controller must remain visible and tracked",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "public-assets-cache-preserved",
                "focus_pattern": "/cache/",
                "path": "public/assets/cache/logo.min.css",
                "role": "tracked_input",
                "description": "Public assets cache is NOT ignored due to root anchoring of /cache/",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
            {
                "id": "config-dev-notes-nearmiss",
                "focus_pattern": "/config/development/",
                "path": "config/development_notes.txt",
                "role": "near_miss",
                "description": "Regular file matching prefix but not directory is NOT ignored",
                "expected": {"ignored": False, "pattern": None, "rule_line": None},
            },
        ]

        # Create files
        for tc in test_cases:
            fp = os.path.join(temp_dir, tc["path"])
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write(f"content of {tc['path']}")

        results = []
        all_passed = True

        print(f"Running git check-ignore verification for {os.path.basename(TEMPLATE_PATH)}...")
        print(f"Tool versions: Git: {get_git_version()}, Python: {platform.python_version()}\n")

        for tc in test_cases:
            actual = check_ignore(temp_dir, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            ) and (
                tc["expected"]["rule_line"] is None or actual["rule_line"] == tc["expected"]["rule_line"]
            )

            if force_fail and tc["id"] == "cache-volt-output":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            rule_str = f"line {actual['rule_line']}:{actual['pattern']}" if actual['ignored'] else "not ignored"
            print(
                f"[{status_str}] [{tc['role']:<15}] {tc['id']:<28} | Path: {tc['path']:<35} | Rule: {rule_str}"
            )

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "role": tc["role"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t020_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            os.makedirs(os.path.join(tracked_repo, "cache"), exist_ok=True)
            tf = os.path.join(tracked_repo, "cache", "bootstrap_cache.php")
            with open(tf, "w") as f:
                f.write("<?php return []; ?>\n")
            run_command(["git", "add", "cache/bootstrap_cache.php"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked bootstrap cache"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tf, "a") as f:
                f.write("<?php // updated cache ?>\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M cache/bootstrap_cache.php" in status_out
            if not tracked_shows_modified:
                all_passed = False

            print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status detects modifications to tracked bootstrap cache")
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T020",
            "template": "Phalcon.gitignore",
            "focus_patterns": ["/cache/", "/config/development/"],
            "tool_versions": {
                "git": get_git_version(),
                "python": sys.version,
                "platform": platform.platform(),
            },
            "assertions": results,
            "tracked_file_check": {
                "passed": tracked_shows_modified,
                "status_output": status_out.strip(),
            },
            "summary": {
                "total": len(results) + 1,
                "passed": sum(1 for r in results if r["passed"]) + (1 if tracked_shows_modified else 0),
                "failed": sum(1 for r in results if not r["passed"]) + (0 if tracked_shows_modified else 1),
                "all_passed": all_passed,
            },
        }

        os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
        with open(EVIDENCE_PATH, "w") as f:
            json.dump(evidence_data, f, indent=2)

        print(f"\nSaved evidence to {EVIDENCE_PATH}")
        print(f"Summary: {evidence_data['summary']['passed']}/{evidence_data['summary']['total']} checks passed.")

        if not all_passed:
            sys.exit(1)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
