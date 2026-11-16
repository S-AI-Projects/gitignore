#!/usr/bin/env python3
"""
Verification check for R46-T018 (Issue #18):
Template: Scala.gitignore
Focus patterns: *.class, *.tasty, *.log

Builds a reusable regression check for Scala.gitignore:
- Verifies compilation artifacts (*.class, *.tasty, *.log) are properly ignored.
- Verifies legitimate source files, build scripts, and near-misses remain visible.
- Asserts tracked-file behavior using git status --porcelain.
Outputs results to work/R46-T018/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Scala.gitignore")
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
    force_fail = os.environ.get("R46_T018_FORCE_FAIL", "0") == "1"

    temp_dir = tempfile.mkdtemp(prefix="sai_t018_")
    try:
        run_command(["git", "init", "-b", "main"], temp_dir)
        run_command(["git", "config", "user.name", "Tester"], temp_dir)
        run_command(["git", "config", "user.email", "tester@example.com"], temp_dir)

        shutil.copyfile(TEMPLATE_PATH, os.path.join(temp_dir, ".gitignore"))

        test_cases = [
            # Matching compilation artifacts
            {
                "id": "class-root-match",
                "focus_pattern": "*.class",
                "path": "App.class",
                "category": "build_artifact",
                "description": "Compiled root bytecode class is ignored",
                "expected": {"ignored": True, "pattern": "*.class"},
            },
            {
                "id": "class-nested-match",
                "focus_pattern": "*.class",
                "path": "target/scala-3.3.0/classes/Main.class",
                "category": "build_artifact",
                "description": "Nested compilation class is ignored",
                "expected": {"ignored": True, "pattern": "*.class"},
            },
            {
                "id": "tasty-root-match",
                "focus_pattern": "*.tasty",
                "path": "App.tasty",
                "category": "build_artifact",
                "description": "Scala 3 TASTy artifact at root is ignored",
                "expected": {"ignored": True, "pattern": "*.tasty"},
            },
            {
                "id": "tasty-nested-match",
                "focus_pattern": "*.tasty",
                "path": "target/scala-3.3.0/classes/Main.tasty",
                "category": "build_artifact",
                "description": "Nested Scala 3 TASTy artifact is ignored",
                "expected": {"ignored": True, "pattern": "*.tasty"},
            },
            {
                "id": "log-root-match",
                "focus_pattern": "*.log",
                "path": "sbt.log",
                "category": "build_artifact",
                "description": "Root build log output is ignored",
                "expected": {"ignored": True, "pattern": "*.log"},
            },
            {
                "id": "log-nested-match",
                "focus_pattern": "*.log",
                "path": "logs/application.log",
                "category": "build_artifact",
                "description": "Nested application log is ignored",
                "expected": {"ignored": True, "pattern": "*.log"},
            },
            # Nonmatching source files & configs that must remain visible
            {
                "id": "source-scala-main",
                "focus_pattern": "*.class",
                "path": "src/main/scala/Main.scala",
                "category": "source_code",
                "description": "Main Scala source file must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "source-scala-test",
                "focus_pattern": "*.class",
                "path": "src/test/scala/AppSuite.scala",
                "category": "source_code",
                "description": "Test suite Scala file must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "build-sbt-definition",
                "focus_pattern": "*.class",
                "path": "build.sbt",
                "category": "build_definition",
                "description": "SBT build definition must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "project-build-properties",
                "focus_pattern": "*.class",
                "path": "project/build.properties",
                "category": "build_definition",
                "description": "SBT build properties must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "resource-logback-xml",
                "focus_pattern": "*.log",
                "path": "src/main/resources/logback.xml",
                "category": "configuration",
                "description": "Logging configuration XML must remain visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "nearmiss-class-name",
                "focus_pattern": "*.class",
                "path": "Class.scala",
                "category": "near_miss",
                "description": "Scala source file containing Class in basename remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "nearmiss-tasty-name",
                "focus_pattern": "*.tasty",
                "path": "TastyRecipe.scala",
                "category": "near_miss",
                "description": "Scala source file containing tasty in basename remains visible",
                "expected": {"ignored": False, "pattern": None},
            },
            {
                "id": "nearmiss-log-name",
                "focus_pattern": "*.log",
                "path": "Logger.scala",
                "category": "near_miss",
                "description": "Scala source file containing log in basename remains visible",
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

            if force_fail and tc["id"] == "class-root-match":
                tc_passed = False

            if not tc_passed:
                all_passed = False

            status_str = "PASS" if tc_passed else "FAIL"
            print(
                f"[{status_str}] [{tc['category']:<16}] {tc['id']:<24} | Path: {tc['path']:<38} | Ignored: {actual['ignored']} (expected {tc['expected']['ignored']})"
            )

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["focus_pattern"],
                "category": tc["category"],
                "path": tc["path"],
                "description": tc["description"],
                "expected": tc["expected"],
                "actual": actual,
                "passed": tc_passed,
            })

        # Tracked file verification
        tracked_repo = tempfile.mkdtemp(prefix="sai_t018_tracked_")
        try:
            run_command(["git", "init", "-b", "main"], tracked_repo)
            run_command(["git", "config", "user.name", "Tester"], tracked_repo)
            run_command(["git", "config", "user.email", "tester@example.com"], tracked_repo)

            tf = os.path.join(tracked_repo, "Prebuilt.class")
            with open(tf, "w") as f:
                f.write("binary v1\n")
            run_command(["git", "add", "Prebuilt.class"], tracked_repo)
            run_command(["git", "commit", "-m", "Commit tracked class"], tracked_repo)

            shutil.copyfile(TEMPLATE_PATH, os.path.join(tracked_repo, ".gitignore"))

            with open(tf, "a") as f:
                f.write("binary v2\n")

            ret, status_out, _ = run_command(["git", "status", "--porcelain"], tracked_repo)
            tracked_shows_modified = "M Prebuilt.class" in status_out
            if not tracked_shows_modified:
                all_passed = False

            print(f"\n[{'PASS' if tracked_shows_modified else 'FAIL'}] Tracked file behavior: status detects modifications to tracked Prebuilt.class")
        finally:
            shutil.rmtree(tracked_repo, ignore_errors=True)

        evidence_data = {
            "task_id": "R46-T018",
            "template": "Scala.gitignore",
            "focus_patterns": ["*.class", "*.tasty", "*.log"],
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
