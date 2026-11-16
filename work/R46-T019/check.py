#!/usr/bin/env python3
"""
Verification check for R46-T019 (Issue #19):
Template: Perl.gitignore
Focus patterns: .last_cover_stats, /META.yml, /META.json

Compares existing rule (/META.yml) with deliberately broader (META.yml)
and narrower (dist/META.yml) alternatives:
- Demonstrates false positive with broader rule (accidental ignoring of t/fixtures/META.yml).
- Demonstrates false negative with narrower rule (failure to ignore root META.yml).
- Tests positive and near-miss fixtures for Perl.gitignore.
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T019/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Perl.gitignore")
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
    force_fail = os.environ.get("R46_T019_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t019_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Standard template matching fixtures
            {
                "id": "last-cover-root-match",
                "focus_pattern": ".last_cover_stats",
                "path": ".last_cover_stats",
                "description": "Root .last_cover_stats cache file is ignored",
                "expected": {"ignored": True, "pattern": ".last_cover_stats"},
            },
            {
                "id": "last-cover-nested-match",
                "focus_pattern": ".last_cover_stats",
                "path": "t/.last_cover_stats",
                "description": "Nested .last_cover_stats cache is ignored by unanchored rule",
                "expected": {"ignored": True, "pattern": ".last_cover_stats"},
            },
            {
                "id": "meta-yml-root-match",
                "focus_pattern": "/META.yml",
                "path": "META.yml",
                "description": "Root generated CPAN META.yml is ignored",
                "expected": {"ignored": True, "pattern": "/META.yml"},
            },
            {
                "id": "meta-json-root-match",
                "focus_pattern": "/META.json",
                "path": "META.json",
                "description": "Root generated CPAN META.json is ignored",
                "expected": {"ignored": True, "pattern": "/META.json"},
            },
            # Near-miss negative fixtures / preserved files
            {
                "id": "meta-yml-fixture-visible",
                "focus_pattern": "/META.yml",
                "path": "t/fixtures/META.yml",
                "description": "Nested test fixture META.yml is NOT ignored due to root anchoring",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "meta-json-fixture-visible",
                "focus_pattern": "/META.json",
                "path": "t/fixtures/META.json",
                "description": "Nested test fixture META.json is NOT ignored due to root anchoring",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "last-cover-txt-nearmiss",
                "focus_pattern": ".last_cover_stats",
                "path": "last_cover_stats.txt",
                "description": "Near-miss file without leading dot is not ignored",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "source-pm-visible",
                "focus_pattern": "/META.yml",
                "path": "lib/App/MyModule.pm",
                "description": "Legitimate Perl module source file is not ignored",
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

            if force_fail and tc["id"] == "last-cover-root-match":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] {tc['id']:<28} | Path: {tc['path']:<26} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})"
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

        # Rule Comparison Demonstration:
        # Existing (/META.yml) vs Broader (META.yml) vs Narrower (dist/META.yml)
        comparison_dir = tempfile.mkdtemp(prefix="sai_t019_comp_")
        try:
            run_command(["git", "init", "-b", "main"], comparison_dir)
            root_meta = "META.yml"
            nested_fixture = "t/fixtures/META.yml"

            for p in [root_meta, nested_fixture]:
                fp = os.path.join(comparison_dir, p)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, "w") as f:
                    f.write("test yml")

            # 1. Broader Rule: META.yml (unanchored)
            with open(os.path.join(comparison_dir, ".gitignore"), "w") as f:
                f.write("META.yml\n")
            act_broad_nested = check_ignore(comparison_dir, nested_fixture)
            # False Positive: t/fixtures/META.yml is erroneously ignored!
            is_false_positive = act_broad_nested["ignored"] is True
            print(f"\n[{'PASS' if is_false_positive else 'FAIL'}] Broader rule 'META.yml' causes False Positive: erroneously ignores '{nested_fixture}'")

            # 2. Narrower Rule: dist/META.yml
            with open(os.path.join(comparison_dir, ".gitignore"), "w") as f:
                f.write("dist/META.yml\n")
            act_narrow_root = check_ignore(comparison_dir, root_meta)
            # False Negative: root META.yml is NOT ignored!
            is_false_negative = act_narrow_root["ignored"] is False
            print(f"[{'PASS' if is_false_negative else 'FAIL'}] Narrower rule 'dist/META.yml' causes False Negative: fails to ignore generated '{root_meta}'")

            # 3. Existing Anchored Rule: /META.yml
            with open(os.path.join(comparison_dir, ".gitignore"), "w") as f:
                f.write("/META.yml\n")
            act_exact_root = check_ignore(comparison_dir, root_meta)
            act_exact_nested = check_ignore(comparison_dir, nested_fixture)
            exact_correct = (act_exact_root["ignored"] is True) and (act_exact_nested["ignored"] is False)
            print(f"[{'PASS' if exact_correct else 'FAIL'}] Existing rule '/META.yml' is optimal: ignores '{root_meta}' and preserves '{nested_fixture}'")

            comp_passed = is_false_positive and is_false_negative and exact_correct
            if not comp_passed:
                all_passed = False

            comparison_report = {
                "broader_rule": {
                    "rule": "META.yml",
                    "nested_fixture_ignored": act_broad_nested["ignored"],
                    "false_positive_demonstrated": is_false_positive,
                },
                "narrower_rule": {
                    "rule": "dist/META.yml",
                    "root_meta_ignored": act_narrow_root["ignored"],
                    "false_negative_demonstrated": is_false_negative,
                },
                "existing_rule": {
                    "rule": "/META.yml",
                    "root_meta_ignored": act_exact_root["ignored"],
                    "nested_fixture_ignored": act_exact_nested["ignored"],
                    "optimal_behavior_verified": exact_correct,
                },
                "passed": comp_passed,
            }
        finally:
            shutil.rmtree(comparison_dir, ignore_errors=True)

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t019_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            tf = os.path.join(tracked_repo, "META.yml")
            with open(tf, "w") as f:
                f.write("name: App\nversion: 1.0\n")
            run_command(["git", "add", "META.yml"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked META.yml"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tf, "a") as f:
                f.write("author: Developer\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M META.yml" in status_out
            if not tracked_shows_modified:
                all_passed = False

            print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status detects modifications to tracked META.yml")
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T019",
            "template": "Perl.gitignore",
            "focus_patterns": [".last_cover_stats", "/META.yml", "/META.json"],
            "tool_versions": {
                "git": get_git_version(),
                "python": sys.version,
                "platform": platform.platform(),
            },
            "assertions": results,
            "rule_narrowness_comparison": comparison_report,
            "tracked_file_check": {
                "passed": tracked_shows_modified,
                "status_output": status_out.strip(),
            },
            "summary": {
                "total": len(results) + 2,
                "passed": sum(1 for r in results if r["passed"]) + (1 if comp_passed else 0) + (1 if tracked_shows_modified else 0),
                "failed": sum(1 for r in results if not r["passed"]) + (0 if comp_passed else 1) + (0 if tracked_shows_modified else 1),
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
