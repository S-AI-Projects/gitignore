#!/usr/bin/env python3
"""
Verification check for R46-T012 (Issue #12):
Template: ecu.test.gitignore
Focus patterns: .workspace/ETdrive.xml, .workspace/favorites.xml, .workspace/filters.xml

Demonstrates nested path matching and anchoring:
Places equivalent filenames at root and two nested directories,
verifying that rules with interior slashes are anchored to the gitignore level,
while unanchored rules match across all directory levels.
Outputs results to work/R46-T012/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "ecu.test.gitignore")
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
    force_fail = os.environ.get("R46_T012_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t012_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Root fixtures (anchored - should match)
            {
                "id": "etdrive-root-match",
                "focus_pattern": ".workspace/ETdrive.xml",
                "path": ".workspace/ETdrive.xml",
                "depth": "root",
                "description": "Anchored rule matches .workspace/ETdrive.xml at root",
                "expected": {"ignored": True, "pattern": ".workspace/ETdrive.xml"},
            },
            {
                "id": "favorites-root-match",
                "focus_pattern": ".workspace/favorites.xml",
                "path": ".workspace/favorites.xml",
                "depth": "root",
                "description": "Anchored rule matches .workspace/favorites.xml at root",
                "expected": {"ignored": True, "pattern": ".workspace/favorites.xml"},
            },
            {
                "id": "filters-root-match",
                "focus_pattern": ".workspace/filters.xml",
                "path": ".workspace/filters.xml",
                "depth": "root",
                "description": "Anchored rule matches .workspace/filters.xml at root",
                "expected": {"ignored": True, "pattern": ".workspace/filters.xml"},
            },
            # Root near-miss without .workspace directory
            {
                "id": "etdrive-root-nearmiss",
                "focus_pattern": ".workspace/ETdrive.xml",
                "path": "ETdrive.xml",
                "depth": "root",
                "description": "Equivalent basename at root without directory prefix is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "favorites-root-nearmiss",
                "focus_pattern": ".workspace/favorites.xml",
                "path": "favorites.xml",
                "depth": "root",
                "description": "Equivalent basename at root without directory prefix is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            # Nested directory 1 (depth 1) - anchored rules must NOT match
            {
                "id": "etdrive-nested-depth1",
                "focus_pattern": ".workspace/ETdrive.xml",
                "path": "subproject/.workspace/ETdrive.xml",
                "depth": "nested_1",
                "description": "Anchored rule does NOT match in nested directory depth 1",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "favorites-nested-depth1",
                "focus_pattern": ".workspace/favorites.xml",
                "path": "subproject/.workspace/favorites.xml",
                "depth": "nested_1",
                "description": "Anchored rule does NOT match in nested directory depth 1",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "filters-nested-depth1",
                "focus_pattern": ".workspace/filters.xml",
                "path": "subproject/.workspace/filters.xml",
                "depth": "nested_1",
                "description": "Anchored rule does NOT match in nested directory depth 1",
                "expected": {"ignored": False, "pattern": None},
            },
            # Nested directory 2 (depth 2) - anchored rules must NOT match
            {
                "id": "etdrive-nested-depth2",
                "focus_pattern": ".workspace/ETdrive.xml",
                "path": "tests/integration/.workspace/ETdrive.xml",
                "depth": "nested_2",
                "description": "Anchored rule does NOT match in nested directory depth 2",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "favorites-nested-depth2",
                "focus_pattern": ".workspace/favorites.xml",
                "path": "tests/integration/.workspace/favorites.xml",
                "depth": "nested_2",
                "description": "Anchored rule does NOT match in nested directory depth 2",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "filters-nested-depth2",
                "focus_pattern": ".workspace/filters.xml",
                "path": "tests/integration/.workspace/filters.xml",
                "depth": "nested_2",
                "description": "Anchored rule does NOT match in nested directory depth 2",
                "expected": {"ignored": False, "pattern": None},
            },
            # Comparison: Unanchored rule (*.arxml) applies anywhere
            {
                "id": "unanchored-root-match",
                "focus_pattern": "*.arxml",
                "path": "package.arxml",
                "depth": "root",
                "description": "Unanchored rule matches at root",
                "expected": {"ignored": True, "pattern": "*.arxml"},
            },
            {
                "id": "unanchored-nested-depth1-match",
                "focus_pattern": "*.arxml",
                "path": "subproject/package.arxml",
                "depth": "nested_1",
                "description": "Unanchored rule matches at nested depth 1",
                "expected": {"ignored": True, "pattern": "*.arxml"},
            },
            {
                "id": "unanchored-nested-depth2-match",
                "focus_pattern": "*.arxml",
                "path": "tests/integration/package.arxml",
                "depth": "nested_2",
                "description": "Unanchored rule matches at nested depth 2",
                "expected": {"ignored": True, "pattern": "*.arxml"},
            },
        ]

        # Create necessary fixture directories and files
        for case in test_cases:
            full_path = os.path.join(temp_dir, case["path"])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write("content")

        results = []
        all_passed = True

        print(f"Running git check-ignore verification for {os.path.basename(TEMPLATE_PATH)}...")
        print(f"Tool versions: Git: {get_git_version()}, Python: {platform.python_version()}\n")

        for tc in test_cases:
            actual = check_ignore(temp_dir, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            )

            if force_fail and tc["id"] == "etdrive-root-match":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<32} | Path: {tc['path']:<38} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']}) | Pattern: {actual['pattern']} (expected {tc['expected']['pattern']})"
            )

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "path": tc["path"],
                "depth": tc["depth"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t012_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            os.makedirs(os.path.join(tracked_repo, ".workspace"), exist_ok=True)
            tracked_file = os.path.join(tracked_repo, ".workspace", "ETdrive.xml")
            with open(tracked_file, "w") as f:
                f.write("original version\n")
            run_command(["git", "add", ".workspace/ETdrive.xml"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked workspace settings"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tracked_file, "a") as f:
                f.write("modified version\n")

            untracked_file = os.path.join(tracked_repo, ".workspace", "favorites.xml")
            with open(untracked_file, "w") as f:
                f.write("untracked favorites\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M .workspace/ETdrive.xml" in status_out
            untracked_is_ignored = ".workspace/favorites.xml" not in status_out

            tracked_passed = tracked_shows_modified and untracked_is_ignored
            if not tracked_passed:
                all_passed = False

            print(f"\n[{'PASS' if tracked_passed else 'FAIL'}] Tracked file behavior: status reports modification to tracked .workspace/ETdrive.xml")

            evidence_data = {
                "task_id": "R46-T012",
                "template": "ecu.test.gitignore",
                "focus_patterns": [".workspace/ETdrive.xml", ".workspace/favorites.xml", ".workspace/filters.xml"],
                "tool_versions": {
                    "git": get_git_version(),
                    "python": sys.version,
                    "platform": platform.platform(),
                },
                "tracked_file_check": {
                    "passed": tracked_passed,
                    "status_output": status_out.strip(),
                    "tracked_modified_visible": tracked_shows_modified,
                    "untracked_ignored": untracked_is_ignored,
                },
                "assertions": results,
                "summary": {
                    "total": len(results) + 1,
                    "passed": sum(1 for r in results if r["passed"]) + (1 if tracked_passed else 0),
                    "failed": sum(1 for r in results if not r["passed"]) + (0 if tracked_passed else 1),
                    "all_passed": all_passed,
                },
            }

            os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
            with open(EVIDENCE_PATH, "w") as f:
                json.dump(evidence_data, f, indent=2)

            print(f"\nSaved evidence to {EVIDENCE_PATH}")
            print(f"Summary: {evidence_data['summary']['passed']}/{evidence_data['summary']['total']} checks passed.")

        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        if not all_passed:
            sys.exit(1)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
