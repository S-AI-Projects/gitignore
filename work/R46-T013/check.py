#!/usr/bin/env python3
"""
Verification check for R46-T013 (Issue #13):
Template: Ada.gitignore
Focus patterns: *.o, *.ali

Demonstrates negation precedence and last-match behavior in Git:
- Tests standard positive and negative fixtures for Ada.gitignore.
- Tests negation order: *.o followed by !prebuilt.o re-includes the file.
- Tests reversed order: !prebuilt.o followed by *.o ignores the file.
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T013/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Ada.gitignore")
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
    force_fail = os.environ.get("R46_T013_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t013_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Positive fixtures
            {
                "id": "o-match-root",
                "focus_pattern": "*.o",
                "path": "main.o",
                "description": "Compiled object file at root is ignored",
                "expected": {"ignored": True, "pattern": "*.o"},
            },
            {
                "id": "o-match-nested",
                "focus_pattern": "*.o",
                "path": "build/sub.o",
                "description": "Compiled object file in nested directory is ignored",
                "expected": {"ignored": True, "pattern": "*.o"},
            },
            {
                "id": "ali-match-root",
                "focus_pattern": "*.ali",
                "path": "main.ali",
                "description": "GNAT Ada library info file at root is ignored",
                "expected": {"ignored": True, "pattern": "*.ali"},
            },
            {
                "id": "ali-match-nested",
                "focus_pattern": "*.ali",
                "path": "build/sub.ali",
                "description": "GNAT Ada library info file in nested directory is ignored",
                "expected": {"ignored": True, "pattern": "*.ali"},
            },
            # Nonmatching source files & near misses
            {
                "id": "source-adb-visible",
                "focus_pattern": "*.o",
                "path": "main.adb",
                "description": "Ada body source file must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "source-ads-visible",
                "focus_pattern": "*.ali",
                "path": "main.ads",
                "description": "Ada spec source file must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "nearmiss-o-txt",
                "focus_pattern": "*.o",
                "path": "prebuilt.o.txt",
                "description": "Near miss with additional .txt extension remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "nearmiss-ali-bak",
                "focus_pattern": "*.ali",
                "path": "data.ali.bak",
                "description": "Near miss with additional .bak extension remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
        ]

        # Create files
        for tc in test_cases:
            full_path = os.path.join(temp_dir, tc["path"])
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

            if force_fail and tc["id"] == "o-match-root":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<24} | Path: {tc['path']:<22} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']}) | Pattern: {actual['pattern']} (expected {tc['expected']['pattern']})"
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

        # Negation Precedence Demonstration
        negation_dir = tempfile.mkdtemp(prefix="sai_t013_neg_")
        try:
            run_command(["git", "init", "-b", "main"], negation_dir)
            with open(os.path.join(negation_dir, "prebuilt.o"), "w") as f:
                f.write("prebuilt binary")
            with open(os.path.join(negation_dir, "other.o"), "w") as f:
                f.write("other binary")

            # Sequence A: *.o followed by !prebuilt.o (negation takes precedence)
            with open(os.path.join(negation_dir, ".gitignore"), "w") as f:
                f.write("*.o\n!prebuilt.o\n")

            act_prebuilt_a = check_ignore(negation_dir, "prebuilt.o")
            act_other_a = check_ignore(negation_dir, "other.o")

            # In Git: check-ignore outputs the negation pattern (!prebuilt.o) when re-included
            neg_a_passed = (act_prebuilt_a["pattern"] == "!prebuilt.o") and (act_other_a["pattern"] == "*.o")

            print(f"\n[{'PASS' if neg_a_passed else 'FAIL'}] Negation sequence A (*.o then !prebuilt.o): prebuilt.o un-ignored, other.o ignored")

            # Sequence B: !prebuilt.o followed by *.o (*.o overrides negation)
            with open(os.path.join(negation_dir, ".gitignore"), "w") as f:
                f.write("!prebuilt.o\n*.o\n")

            act_prebuilt_b = check_ignore(negation_dir, "prebuilt.o")
            neg_b_passed = (act_prebuilt_b["ignored"] is True and act_prebuilt_b["pattern"] == "*.o")

            print(f"[{'PASS' if neg_b_passed else 'FAIL'}] Negation sequence B (!prebuilt.o then *.o): *.o overrides negation, prebuilt.o ignored")

            if not (neg_a_passed and neg_b_passed):
                all_passed = False

            negation_results = {
                "sequence_A": {
                    "rules": ["*.o", "!prebuilt.o"],
                    "prebuilt_o": act_prebuilt_a,
                    "other_o": act_other_a,
                    "passed": neg_a_passed,
                },
                "sequence_B": {
                    "rules": ["!prebuilt.o", "*.o"],
                    "prebuilt_o": act_prebuilt_b,
                    "passed": neg_b_passed,
                },
            }
        finally:
            shutil.rmtree(negation_dir, ignore_errors=True)

        # Tracked files check
        tracked_dir = tempfile.mkdtemp(prefix="sai_t013_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_dir)
            run_command(["git", "config", "user.name", "Tester"], tracked_dir)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_dir)

            tracked_o = os.path.join(tracked_dir, "main.o")
            with open(tracked_o, "w") as f:
                f.write("initial obj\n")
            run_command(["git", "add", "main.o"], tracked_dir)
            run_command(["git", "commit", "-m", "Commit tracked obj"], tracked_dir)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_dir, ".gitignore"))

            with open(tracked_o, "a") as f:
                f.write("updated obj\n")

            untracked_o = os.path.join(tracked_dir, "second.o")
            with open(untracked_o, "w") as f:
                f.write("untracked obj\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_dir)
            tracked_shows_modified = "M main.o" in status_out
            untracked_is_ignored = "second.o" not in status_out

            tracked_passed = tracked_shows_modified and untracked_is_ignored
            if not tracked_passed:
                all_passed = False

            print(f"[{'PASS' if tracked_passed else 'FAIL'}] Tracked file behavior: status reports modification to tracked main.o")
        finally:
            shutil.rmtree(tracked_dir, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T013",
            "template": "Ada.gitignore",
            "focus_patterns": ["*.o", "*.ali"],
            "tool_versions": {
                "git": get_git_version(),
                "python": sys.version,
                "platform": platform.platform(),
            },
            "assertions": results,
            "negation_order_demonstration": negation_results,
            "tracked_file_check": {
                "passed": tracked_passed,
                "status_output": status_out.strip(),
            },
            "summary": {
                "total": len(results) + 3,
                "passed": sum(1 for r in results if r["passed"]) + (1 if neg_a_passed else 0) + (1 if neg_b_passed else 0) + (1 if tracked_passed else 0),
                "failed": sum(1 for r in results if not r["passed"]) + (0 if (neg_a_passed and neg_b_passed and tracked_passed) else 1),
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
