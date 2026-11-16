#!/usr/bin/env python3
"""
Verification check for R46-T015 (Issue #15):
Template: Global/Windows.gitignore
Focus patterns: Thumbs.db, Thumbs.db:encryptable, ehthumbs.db

Demonstrates tracked-file behavior vs untracked-file ignore behavior:
- Tests positive and near-miss fixtures for each focus pattern.
- Commits a matching fixture (Thumbs.db) BEFORE applying the template.
- Modifies the tracked fixture and introduces an untracked matching fixture (ehthumbs.db).
- Proves why ignore rules do not retroactively untrack files.
Outputs results to work/R46-T015/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Global", "Windows.gitignore")
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
    force_fail = os.environ.get("R46_T015_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t015_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Matching fixtures
            {
                "id": "thumbs-root-match",
                "focus_pattern": "Thumbs.db",
                "path": "Thumbs.db",
                "description": "Root Windows thumbnail cache is ignored",
                "expected": {"ignored": True, "pattern": "Thumbs.db"},
            },
            {
                "id": "thumbs-nested-match",
                "focus_pattern": "Thumbs.db",
                "path": "assets/Thumbs.db",
                "description": "Nested Windows thumbnail cache is ignored",
                "expected": {"ignored": True, "pattern": "Thumbs.db"},
            },
            {
                "id": "thumbs-encryptable-match",
                "focus_pattern": "Thumbs.db:encryptable",
                "path": "Thumbs.db:encryptable",
                "description": "Thumbs.db:encryptable alternate stream file is ignored",
                "expected": {"ignored": True, "pattern": "Thumbs.db:encryptable"},
            },
            {
                "id": "ehthumbs-root-match",
                "focus_pattern": "ehthumbs.db",
                "path": "ehthumbs.db",
                "description": "Windows Media Center thumbnail cache is ignored",
                "expected": {"ignored": True, "pattern": "ehthumbs.db"},
            },
            {
                "id": "ehthumbs-nested-match",
                "focus_pattern": "ehthumbs.db",
                "path": "media/ehthumbs.db",
                "description": "Nested Windows Media Center thumbnail cache is ignored",
                "expected": {"ignored": True, "pattern": "ehthumbs.db"},
            },
            # Nonmatching near-misses
            {
                "id": "thumbs-ext-nearmiss",
                "focus_pattern": "Thumbs.db",
                "path": "Thumbs.db.txt",
                "description": "Near miss with .txt extension remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "thumbs-prefix-nearmiss",
                "focus_pattern": "Thumbs.db",
                "path": "MyThumbs.db",
                "description": "Near miss with prefix My is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "ehthumbs-bak-nearmiss",
                "focus_pattern": "ehthumbs.db",
                "path": "ehthumbs.db.bak",
                "description": "Near miss with .bak extension is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "thumbs-png-nearmiss",
                "focus_pattern": "Thumbs.db",
                "path": "Thumbs.png",
                "description": "User image file is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
        ]

        # Create files
        for tc in test_cases:
            fp = os.path.join(temp_dir, tc["path"])
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write("test content")

        results = []
        all_passed = True

        print(f"Running git check-ignore verification for {os.path.basename(TEMPLATE_PATH)}...")
        print(f"Tool versions: Git: {get_git_version()}, Python: {platform.python_version()}\n")

        for tc in test_cases:
            actual = check_ignore(temp_dir, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            )

            if force_fail and tc["id"] == "thumbs-root-match":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<26} | Path: {tc['path']:<24} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']}) | Pattern: {actual['pattern']} (expected {tc['expected']['pattern']})"
            )

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })

        # Tracked vs Untracked demonstration repo
        tracked_repo = tempfile.mkdtemp(prefix="sai_t015_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            # Step 1: Commit Thumbs.db BEFORE applying the ignore template
            tracked_file = os.path.join(tracked_repo, "Thumbs.db")
            with open(tracked_file, "w") as f:
                f.write("committed thumbnail cache v1\n")
            run_command(["git", "add", "Thumbs.db"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit pre-existing Thumbs.db"], tracked_repo)

            # Step 2: Now apply Global/Windows.gitignore
            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            # Step 3: Modify tracked Thumbs.db
            with open(tracked_file, "a") as f:
                f.write("committed thumbnail cache v2 modification\n")

            # Step 4: Create untracked matching fixture ehthumbs.db
            untracked_file = os.path.join(tracked_repo, "ehthumbs.db")
            with open(untracked_file, "w") as f:
                f.write("untracked ehthumbs cache\n")

            # Step 5: Check git status
            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)

            # Assertions:
            # - Tracked Thumbs.db MUST appear as modified ' M Thumbs.db'
            # - Untracked ehthumbs.db MUST NOT appear (is ignored)
            tracked_visible_as_modified = "M Thumbs.db" in status_out
            untracked_ignored = "ehthumbs.db" not in status_out

            tracked_test_passed = tracked_visible_as_modified and untracked_ignored
            if not tracked_test_passed:
                all_passed = False

            print(f"\n[{'PASS' if tracked_test_passed else 'FAIL'}] Tracked file behavior: status detects 'M Thumbs.db' while untracked 'ehthumbs.db' is ignored")

            # Demonstrate git rm --cached untracks the file
            run_command(["git", "rm", "--cached", "Thumbs.db"], tracked_repo)
            ret2, status_after_rm, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            rm_cached_passed = "D  Thumbs.db" in status_after_rm

            print(f"[{'PASS' if rm_cached_passed else 'FAIL'}] Untracking via 'git rm --cached': stages deletion from index while preserving working file")
            if not rm_cached_passed:
                all_passed = False

            tracked_report = {
                "tracked_file": "Thumbs.db",
                "untracked_file": "ehthumbs.db",
                "status_before_untrack": status_out.strip(),
                "status_after_untrack": status_after_rm.strip(),
                "tracked_modification_detected": tracked_visible_as_modified,
                "untracked_ignored": untracked_ignored,
                "untrack_via_rm_cached": rm_cached_passed,
                "passed": tracked_test_passed and rm_cached_passed,
            }
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T015",
            "template": "Global/Windows.gitignore",
            "focus_patterns": ["Thumbs.db", "Thumbs.db:encryptable", "ehthumbs.db"],
            "tool_versions": {
                "git": get_git_version(),
                "python": sys.version,
                "platform": platform.platform(),
            },
            "assertions": results,
            "tracked_file_experiment": tracked_report,
            "summary": {
                "total": len(results) + 2,
                "passed": sum(1 for r in results if r["passed"]) + (2 if tracked_report["passed"] else 0),
                "failed": sum(1 for r in results if not r["passed"]) + (0 if tracked_report["passed"] else 2),
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
