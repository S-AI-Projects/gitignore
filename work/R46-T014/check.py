#!/usr/bin/env python3
"""
Verification check for R46-T014 (Issue #14):
Template: Joomla.gitignore
Focus patterns: /.htaccess, /administrator/cache/*, /administrator/components/com_actionlogs/*

Demonstrates distinguishing directories from files:
- Creates file and directory fixtures with identical basenames in separate repositories.
- Explains the effect of trailing slashes and wildcards (/*) vs bare names (/.htaccess).
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T014/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Joomla.gitignore")
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
        subparts = rule_info.split(":")
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
    force_fail = os.environ.get("R46_T014_FORCE_FAIL", "0") == "1"
    all_passed = True
    results = []

    print(f"Running git check-ignore verification for {os.path.basename(TEMPLATE_PATH)}...")
    print(f"Tool versions: Git: {get_git_version()}, Python: {platform.python_version()}\n")

    # Repository A: File fixtures
    repo_a = tempfile.mkdtemp(prefix="sai_t014_repoA_")
    try:
        run_command(["git", "init", "-b", "main"], repo_a)
        shutil.copyfile(TEMPLATE_PATH, os.path.join(repo_a, ".gitignore"))

        repo_a_cases = [
            {
                "id": "htaccess-file-match",
                "focus_pattern": "/.htaccess",
                "path": ".htaccess",
                "is_dir": False,
                "description": "Root .htaccess as regular file is ignored",
                "expected": {"ignored": True, "pattern": "/.htaccess"},
            },
            {
                "id": "admin-cache-file-match",
                "focus_pattern": "/administrator/cache/*",
                "path": "administrator/cache/output.cache",
                "is_dir": False,
                "description": "Cache output file inside administrator/cache is ignored",
                "expected": {"ignored": True, "pattern": "/administrator/cache/*"},
            },
            {
                "id": "admin-actionlogs-file-match",
                "focus_pattern": "/administrator/components/com_actionlogs/*",
                "path": "administrator/components/com_actionlogs/test.log",
                "is_dir": False,
                "description": "Log file inside administrator actionlogs is ignored",
                "expected": {"ignored": True, "pattern": "/administrator/components/com_actionlogs/*"},
            },
            {
                "id": "htaccess-nested-nearmiss",
                "focus_pattern": "/.htaccess",
                "path": "nested/.htaccess",
                "is_dir": False,
                "description": "Nested .htaccess file is NOT ignored due to leading slash anchoring",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "frontend-actionlogs-nearmiss",
                "focus_pattern": "/administrator/components/com_actionlogs/*",
                "path": "components/com_actionlogs/component.php",
                "is_dir": False,
                "description": "Frontend component file is NOT ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "root-cache-nearmiss",
                "focus_pattern": "/administrator/cache/*",
                "path": "cache_file",
                "is_dir": False,
                "description": "Root cache_file is NOT ignored",
                "expected": {"ignored": False, "pattern": None},
            },
        ]

        for tc in repo_a_cases:
            fp = os.path.join(repo_a, tc["path"])
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write("content")

            actual = check_ignore(repo_a, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            )
            if force_fail and tc["id"] == "htaccess-file-match":
                tc_passed = False
            if not tc_passed:
                all_passed = False

            print(f"[{'PASS' if tc_passed else 'FAIL'}] [RepoA-File] {tc['id']:<28} | Path: {tc['path']:<45} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})")
            results.append({
                "repo": "RepoA_Files",
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })
    finally:
        shutil.rmtree(repo_a, ignore_errors=True)

    # Repository B: Directory fixtures with same basenames
    repo_b = tempfile.mkdtemp(prefix="sai_t014_repoB_")
    try:
        run_command(["git", "init", "-b", "main"], repo_b)
        shutil.copyfile(TEMPLATE_PATH, os.path.join(repo_b, ".gitignore"))

        repo_b_cases = [
            {
                "id": "htaccess-dir-match",
                "focus_pattern": "/.htaccess",
                "path": ".htaccess/nested.conf",
                "description": "Directory named .htaccess is matched by /.htaccess rule without trailing slash",
                "expected": {"ignored": True, "pattern": "/.htaccess"},
            },
            {
                "id": "admin-cache-dir-match",
                "focus_pattern": "/administrator/cache/*",
                "path": "administrator/cache/subdir/item.tmp",
                "description": "Subdirectory inside administrator/cache is matched by wildcard /*",
                "expected": {"ignored": True, "pattern": "/administrator/cache/*"},
            },
            {
                "id": "admin-cache-sibling-nearmiss",
                "focus_pattern": "/administrator/cache/*",
                "path": "administrator/cache_store/item.tmp",
                "description": "Sibling directory cache_store is NOT ignored",
                "expected": {"ignored": False, "pattern": None},
            },
        ]

        for tc in repo_b_cases:
            fp = os.path.join(repo_b, tc["path"])
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write("content")

            actual = check_ignore(repo_b, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            )
            if not tc_passed:
                all_passed = False

            print(f"[{'PASS' if tc_passed else 'FAIL'}] [RepoB-Dir]  {tc['id']:<28} | Path: {tc['path']:<45} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})")
            results.append({
                "repo": "RepoB_Dirs",
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })
    finally:
        shutil.rmtree(repo_b, ignore_errors=True)

    # Tracked file verification
    tracked_repo = tempfile.mkdtemp(prefix="sai_t014_tracked_")
    try:
        run_command(["git", "init", "-b", "main"], tracked_repo)
        run_command(["git", "config", "user.name", "Tester"], tracked_repo)
        run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

        tf = os.path.join(tracked_repo, ".htaccess")
        with open(tf, "w") as f:
            f.write("# initial htaccess\n")
        run_command(["git", "add", ".htaccess"], tracked_repo)
        run_command(["git", "commit", "-m", "Commit initial htaccess"], tracked_repo)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

        with open(tf, "a") as f:
            f.write("# modified htaccess\n")

        ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
        tracked_shows_modified = "M .htaccess" in status_out
        if not tracked_shows_modified:
            all_passed = False

        print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status reports modification to tracked .htaccess")
    finally:
        shutil.rmtree(tracked_repo, ignore_errors=True)

    evidence_data = {
        "task_id": "R46-T014",
        "template": "Joomla.gitignore",
        "focus_patterns": ["/.htaccess", "/administrator/cache/*", "/administrator/components/com_actionlogs/*"],
        "tool_versions": {
            "git": get_git_version(),
            "python": sys.version,
            "platform": platform.platform(),
        },
        "tracked_file_check": {
            "passed": tracked_shows_modified,
            "status_output": status_out.strip(),
        },
        "assertions": results,
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


if __name__ == "__main__":
    main()
