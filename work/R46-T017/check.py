#!/usr/bin/env python3
"""
Verification check for R46-T017 (Issue #17):
Template: OpenCart.gitignore
Focus patterns: .htaccess, /config.php, admin/config.php

Connects each selected rule to the tool/installer output it is intended to hide:
- Distinguishes runtime generated outputs (.htaccess, config.php, admin/config.php)
  from official distributed source templates (htaccess.txt, config-dist.php, admin/config-dist.php).
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T017/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "OpenCart.gitignore")
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
    force_fail = os.environ.get("R46_T017_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t017_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Generated outputs (should be ignored)
            {
                "id": "htaccess-root-output",
                "focus_pattern": ".htaccess",
                "path": ".htaccess",
                "type": "generated_output",
                "description": "Generated Apache rewrite configuration at root is ignored",
                "expected": {"ignored": True, "pattern": ".htaccess"},
            },
            {
                "id": "htaccess-admin-output",
                "focus_pattern": ".htaccess",
                "path": "admin/.htaccess",
                "type": "generated_output",
                "description": "Generated Apache configuration in admin directory is ignored by unanchored rule",
                "expected": {"ignored": True, "pattern": ".htaccess"},
            },
            {
                "id": "config-storefront-output",
                "focus_pattern": "/config.php",
                "path": "config.php",
                "type": "generated_output",
                "description": "Installer-generated storefront config.php is ignored",
                "expected": {"ignored": True, "pattern": "/config.php"},
            },
            {
                "id": "config-admin-output",
                "focus_pattern": "admin/config.php",
                "path": "admin/config.php",
                "type": "generated_output",
                "description": "Installer-generated admin/config.php is ignored",
                "expected": {"ignored": True, "pattern": "admin/config.php"},
            },
            # Legitimate source templates & files (MUST NOT be ignored)
            {
                "id": "htaccess-source-template",
                "focus_pattern": ".htaccess",
                "path": "htaccess.txt",
                "type": "source_template",
                "description": "Distributed htaccess.txt source template must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "config-storefront-template",
                "focus_pattern": "/config.php",
                "path": "config-dist.php",
                "type": "source_template",
                "description": "Distributed config-dist.php source template must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "config-admin-template",
                "focus_pattern": "admin/config.php",
                "path": "admin/config-dist.php",
                "type": "source_template",
                "description": "Distributed admin/config-dist.php source template must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "system-config-source",
                "focus_pattern": "/config.php",
                "path": "system/config.php",
                "type": "source_module",
                "description": "Core system config module is NOT ignored due to root anchoring of /config.php",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "catalog-config-source",
                "focus_pattern": "admin/config.php",
                "path": "catalog/config.php",
                "type": "source_module",
                "description": "Catalog config module is NOT ignored",
                "expected": {"ignored": False, "pattern": None},
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
            )

            if force_fail and tc["id"] == "htaccess-root-output":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] [{tc['type']:<18}] {tc['id']:<26} | Path: {tc['path']:<24} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})"
            )

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "type": tc["type"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t017_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            tf = os.path.join(tracked_repo, "config.php")
            with open(tf, "w") as f:
                f.write("<?php define('DB_USER', 'root'); ?>\n")
            run_command(["git", "add", "config.php"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked config.php"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tf, "a") as f:
                f.write("<?php define('DB_PASS', 'secret'); ?>\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M config.php" in status_out
            if not tracked_shows_modified:
                all_passed = False

            print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status detects modifications to tracked config.php")
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T017",
            "template": "OpenCart.gitignore",
            "focus_patterns": [".htaccess", "/config.php", "admin/config.php"],
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
