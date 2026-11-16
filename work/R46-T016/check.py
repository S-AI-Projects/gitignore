#!/usr/bin/env python3
"""
Verification check for R46-T016 (Issue #16):
Template: Typo3.gitignore
Focus patterns: /fileadmin/user_upload/, /fileadmin/_temp_/, /fileadmin/_processed_/

Tests space-containing paths and case variants;
Records filesystem case behavior and core.ignorecase explicitly.
Outputs results to work/R46-T016/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Typo3.gitignore")
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


def detect_filesystem_case_sensitivity(directory):
    # Detect if underlying filesystem is case sensitive
    probe_lower = os.path.join(directory, "probe_case_test.txt")
    probe_upper = os.path.join(directory, "PROBE_CASE_TEST.TXT")
    try:
        with open(probe_lower, "w") as f:
            f.write("lower")
        is_case_sensitive = not os.path.exists(probe_upper)
    finally:
        if os.path.exists(probe_lower):
            os.remove(probe_lower)
    return is_case_sensitive


def main():
    force_fail = os.environ.get("R46_T016_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t016_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        fs_case_sensitive = detect_filesystem_case_sensitivity(temp_dir)

        test_cases = [
            # Matching fixtures (standard & space-containing)
            {
                "id": "upload-standard-match",
                "focus_pattern": "/fileadmin/user_upload/",
                "path": "fileadmin/user_upload/standard.jpg",
                "description": "Standard file in user_upload is ignored",
                "expected": {"ignored": True, "pattern": "/fileadmin/user_upload/"},
            },
            {
                "id": "upload-spaces-match",
                "focus_pattern": "/fileadmin/user_upload/",
                "path": "fileadmin/user_upload/my company photo 2026.png",
                "description": "File with spaces inside user_upload is ignored",
                "expected": {"ignored": True, "pattern": "/fileadmin/user_upload/"},
            },
            {
                "id": "temp-match",
                "focus_pattern": "/fileadmin/_temp_/",
                "path": "fileadmin/_temp_/session_cache.tmp",
                "description": "File in _temp_ directory is ignored",
                "expected": {"ignored": True, "pattern": "/fileadmin/_temp_/"},
            },
            {
                "id": "processed-spaces-match",
                "focus_pattern": "/fileadmin/_processed_/",
                "path": "fileadmin/_processed_/thumbnail 300 x 300.webp",
                "description": "File with spaces in _processed_ directory is ignored",
                "expected": {"ignored": True, "pattern": "/fileadmin/_processed_/"},
            },
            # Near-miss negative fixtures
            {
                "id": "upload-space-folder-nearmiss",
                "focus_pattern": "/fileadmin/user_upload/",
                "path": "fileadmin/user upload/image.jpg",
                "description": "Directory with space instead of underscore remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "temp-missing-underscores-nearmiss",
                "focus_pattern": "/fileadmin/_temp_/",
                "path": "fileadmin/temp/cache.tmp",
                "description": "Directory without underscores remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "upload-nested-nearmiss",
                "focus_pattern": "/fileadmin/user_upload/",
                "path": "nested/fileadmin/user_upload/image.jpg",
                "description": "Nested directory is not matched due to root leading slash anchoring",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "temp-sibling-file-nearmiss",
                "focus_pattern": "/fileadmin/_temp_/",
                "path": "fileadmin/_temp_.txt",
                "description": "Regular file with matching prefix but not directory is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
        ]

        # Create files
        for tc in test_cases:
            fp = os.path.join(temp_dir, tc["path"])
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write("content")

        results = []
        all_passed = True

        print(f"Running git check-ignore verification for {os.path.basename(TEMPLATE_PATH)}...")
        print(f"Tool versions: Git: {get_git_version()}, Python: {platform.python_version()}\n")
        print(f"Filesystem case sensitivity: {fs_case_sensitive}")

        for tc in test_cases:
            actual = check_ignore(temp_dir, tc["path"])
            tc_passed = (actual["ignored"] == tc["expected"]["ignored"]) and (
                tc["expected"]["pattern"] is None or actual["pattern"] == tc["expected"]["pattern"]
            )

            if force_fail and tc["id"] == "upload-standard-match":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<34} | Path: {tc['path']:<42} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})"
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

        # Explicit core.ignorecase case-variant tests
        case_tests = []
        for ignorecase_setting in [False, True]:
            case_repo = tempfile.mkdtemp(prefix=f"sai_t016_case_{ignorecase_setting}_")
            try:
                run_command(["git", "init", "-b", "main"], case_repo)
                run_command(["git", "config", "core.ignorecase", str(ignorecase_setting).lower()], case_repo)
                shutil.copyfile(TEMPLATE_PATH, os.path.join(case_repo, ".gitignore"))

                variant_path = "Fileadmin/User_Upload/Photo.JPG"
                fp = os.path.join(case_repo, variant_path)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, "w") as f:
                    f.write("case test")

                act = check_ignore(case_repo, variant_path)

                # When core.ignorecase is True, Git treats case variants as matching
                # When core.ignorecase is False, Git treats case variants as NOT matching
                expected_ignored = ignorecase_setting
                case_passed = (act["ignored"] == expected_ignored)
                if not case_passed:
                    all_passed = False

                print(
                    f"[{'PASS' if case_passed else 'FAIL'}] [core.ignorecase={ignorecase_setting:<5}] Case variant '{variant_path}' | Ignored: {act['ignored']} (expected {expected_ignored})"
                )

                case_tests.append({
                    "core_ignorecase": ignorecase_setting,
                    "variant_path": variant_path,
                    "actual": act,
                    "expected_ignored": expected_ignored,
                    "passed": case_passed,
                })
            finally:
                shutil.rmtree(case_repo, ignore_errors=True)

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t016_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            os.makedirs(os.path.join(tracked_repo, "fileadmin", "user_upload"), exist_ok=True)
            tf = os.path.join(tracked_repo, "fileadmin", "user_upload", "placeholder.txt")
            with open(tf, "w") as f:
                f.write("initial placeholder\n")
            run_command(["git", "add", "fileadmin/user_upload/placeholder.txt"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked upload file"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tf, "a") as f:
                f.write("updated placeholder\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M fileadmin/user_upload/placeholder.txt" in status_out
            if not tracked_shows_modified:
                all_passed = False

            print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status detects modifications to tracked upload file")
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T016",
            "template": "Typo3.gitignore",
            "focus_patterns": ["/fileadmin/user_upload/", "/fileadmin/_temp_/", "/fileadmin/_processed_/"],
            "filesystem_info": {
                "platform": platform.platform(),
                "filesystem_case_sensitive": fs_case_sensitive,
            },
            "tool_versions": {
                "git": get_git_version(),
                "python": sys.version,
            },
            "assertions": results,
            "case_sensitivity_checks": case_tests,
            "tracked_file_check": {
                "passed": tracked_shows_modified,
                "status_output": status_out.strip(),
            },
            "summary": {
                "total": len(results) + len(case_tests) + 1,
                "passed": sum(1 for r in results if r["passed"]) + sum(1 for c in case_tests if c["passed"]) + (1 if tracked_shows_modified else 0),
                "failed": sum(1 for r in results if not r["passed"]) + sum(1 for c in case_tests if not c["passed"]) + (0 if tracked_shows_modified else 1),
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
