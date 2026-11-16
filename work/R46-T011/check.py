#!/usr/bin/env python3
"""
Verification check for R46-T011 (Issue #11):
Template: Global/SBT.gitignore
Focus patterns: dist/*, target/, lib_managed/

Asserts classification and matching patterns using `git check-ignore -v --no-index`
and verifies tracked-file behavior using `git status --porcelain`.
Outputs results to work/R46-T011/evidence.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_PATH = os.path.join(REPO_ROOT, "Global", "SBT.gitignore")
EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), "evidence.json")


def run_command(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def main():
    force_fail = os.environ.get("R46_T011_FORCE_FAIL") == "1"

    if not os.path.isfile(TEMPLATE_PATH):
        print(f"Error: Template not found at {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    git_ver_res = subprocess.run(["git", "--version"], capture_output=True, text=True)
    git_version = git_ver_res.stdout.strip()
    python_version = sys.version.split()[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize a temporary git repository
        rc, out, err = run_command(["git", "init"], cwd=tmpdir)
        if rc != 0:
            print(f"Failed to initialize git repository: {err}", file=sys.stderr)
            sys.exit(1)

        # Configure dummy user for committing in temporary repo
        run_command(["git", "config", "user.name", "Test User"], cwd=tmpdir)
        run_command(["git", "config", "user.email", "test@example.com"], cwd=tmpdir)

        # Copy the template to .gitignore
        target_gitignore = os.path.join(tmpdir, ".gitignore")
        shutil.copyfile(TEMPLATE_PATH, target_gitignore)

        # Test cases defining positive and negative fixtures
        # For each focus pattern: positive fixtures and near-miss nonmatching fixtures
        test_cases = [
            # Focus Pattern 1: dist/*
            {
                "id": "dist-match-jar",
                "pattern": "dist/*",
                "rel_path": "dist/bundle.jar",
                "expected_ignored": True,
                "expected_pattern": "dist/*",
                "description": "Standard build distribution artifact inside dist/",
            },
            {
                "id": "dist-match-zip",
                "pattern": "dist/*",
                "rel_path": "dist/release.zip",
                "expected_ignored": True,
                "expected_pattern": "dist/*",
                "description": "Zip archive in distribution folder",
            },
            {
                "id": "dist-nonmatch-file-prefix",
                "pattern": "dist/*",
                "rel_path": "dist.sbt",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Near-miss file sharing 'dist' prefix at root",
            },
            {
                "id": "dist-nonmatch-sibling-dir",
                "pattern": "dist/*",
                "rel_path": "distribution/bundle.jar",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Directory named 'distribution' is not matched by 'dist/*'",
            },
            {
                "id": "dist-nonmatch-nested",
                "pattern": "dist/*",
                "rel_path": "src/dist/bundle.jar",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Nested 'dist/' directory: 'dist/*' contains a slash so anchors to root",
            },
            # Focus Pattern 2: target/
            {
                "id": "target-match-root",
                "pattern": "target/",
                "rel_path": "target/scala-2.13/classes/Main.class",
                "expected_ignored": True,
                "expected_pattern": "target/",
                "description": "Standard sbt output directory at root",
            },
            {
                "id": "target-match-nested",
                "pattern": "target/",
                "rel_path": "project/target/config-classes/Foo.class",
                "expected_ignored": True,
                "expected_pattern": "target/",
                "description": "Nested target directory for sbt build definition",
            },
            {
                "id": "target-nonmatch-regular-file",
                "pattern": "target/",
                "rel_path": "docs/target",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Regular file named 'target' without trailing slash remains visible",
            },
            {
                "id": "target-nonmatch-file-extension",
                "pattern": "target/",
                "rel_path": "target.sbt",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Near-miss sbt file starting with target",
            },
            {
                "id": "target-nonmatch-source-file",
                "pattern": "target/",
                "rel_path": "src/main/scala/Target.scala",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Scala source file containing 'Target' in path",
            },
            # Focus Pattern 3: lib_managed/
            {
                "id": "lib-managed-match-root",
                "pattern": "lib_managed/",
                "rel_path": "lib_managed/jars/org.scala-lang/scala-library.jar",
                "expected_ignored": True,
                "expected_pattern": "lib_managed/",
                "description": "Managed library jar downloaded by sbt",
            },
            {
                "id": "lib-managed-match-subproject",
                "pattern": "lib_managed/",
                "rel_path": "subproject/lib_managed/bundles/plugin.jar",
                "expected_ignored": True,
                "expected_pattern": "lib_managed/",
                "description": "Subproject managed library folder",
            },
            {
                "id": "lib-managed-nonmatch-regular-file",
                "pattern": "lib_managed/",
                "rel_path": "docs/lib_managed",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Regular file named 'lib_managed' without trailing slash",
            },
            {
                "id": "lib-managed-nonmatch-unmanaged",
                "pattern": "lib_managed/",
                "rel_path": "lib/unmanaged.jar",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Unmanaged library directory 'lib/' is preserved and not ignored",
            },
            {
                "id": "lib-managed-nonmatch-near-miss",
                "pattern": "lib_managed/",
                "rel_path": "lib_managed_backup.zip",
                "expected_ignored": False,
                "expected_pattern": None,
                "description": "Archive file starting with lib_managed is not ignored",
            },
        ]

        # Create all test fixtures on filesystem
        for tc in test_cases:
            abs_path = os.path.join(tmpdir, tc["rel_path"])
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w") as f:
                f.write(f"Fixture for {tc['id']}\n")

        results = []
        all_passed = True

        print(f"Running git check-ignore verification for Global/SBT.gitignore...")
        print(f"Tool versions: Git: {git_version}, Python: {python_version}\n")

        for tc in test_cases:
            rel = tc["rel_path"]
            # Run check-ignore
            cmd = ["git", "check-ignore", "-v", "--no-index", rel]
            rc, stdout, stderr = run_command(cmd, cwd=tmpdir)
            stdout = stdout.strip()

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

            passed = (actual_ignored == tc["expected_ignored"])
            if tc["expected_ignored"]:
                if actual_pattern != tc["expected_pattern"]:
                    passed = False

            if force_fail and tc["id"] == "dist-match-jar":
                passed = False

            if not passed:
                all_passed = False

            status_str = "PASS" if passed else "FAIL"
            print(f"[{status_str}] {tc['id']:<35} | Path: {rel:<40} | Ignored: {actual_ignored} (expected {tc['expected_ignored']}) | Pattern: {actual_pattern} (expected {tc['expected_pattern']})")

            results.append({
                "id": tc["id"],
                "focus_pattern": tc["pattern"],
                "path": rel,
                "description": tc["description"],
                "expected": {
                    "ignored": tc["expected_ignored"],
                    "pattern": tc["expected_pattern"],
                },
                "actual": {
                    "returncode": rc,
                    "ignored": actual_ignored,
                    "pattern": actual_pattern,
                    "rule_line": actual_rule_line,
                    "raw_output": stdout,
                },
                "passed": passed,
            })

        # Tracked file behavior verification
        # An already tracked file matching an ignore rule should still be tracked by git
        tracked_rel = "target/pre_existing_tracked_file.txt"
        tracked_abs = os.path.join(tmpdir, tracked_rel)
        os.makedirs(os.path.dirname(tracked_abs), exist_ok=True)
        with open(tracked_abs, "w") as f:
            f.write("tracked content\n")

        run_command(["git", "add", "-f", tracked_rel], cwd=tmpdir)
        run_command(["git", "commit", "-m", "Add tracked file in target/"], cwd=tmpdir)

        # Modify tracked file
        with open(tracked_abs, "a") as f:
            f.write("new change\n")

        rc_status, out_status, _ = run_command(["git", "status", "--porcelain"], cwd=tmpdir)
        tracked_modified_visible = f" M {tracked_rel}" in out_status or f"M  {tracked_rel}" in out_status

        tracked_test = {
            "id": "tracked-file-behavior",
            "description": "Tracked files inside target/ remain visible to git status despite ignore rule",
            "path": tracked_rel,
            "porcelain_status": out_status.strip(),
            "passed": tracked_modified_visible,
        }
        if not tracked_modified_visible:
            all_passed = False

        print(f"\n[{'PASS' if tracked_modified_visible else 'FAIL'}] Tracked file behavior: status --porcelain shows '{tracked_rel}'")

        evidence = {
            "task_id": "R46-T011",
            "item": "Global/SBT.gitignore",
            "focus_patterns": ["dist/*", "target/", "lib_managed/"],
            "tool_versions": {
                "git": git_version,
                "python": python_version,
                "platform": platform.platform(),
            },
            "tracked_file_check": tracked_test,
            "test_cases": results,
            "summary": {
                "total": len(results) + 1,
                "passed": sum(1 for r in results if r["passed"]) + (1 if tracked_modified_visible else 0),
                "failed": sum(1 for r in results if not r["passed"]) + (0 if tracked_modified_visible else 1),
                "all_passed": all_passed,
            },
        }

        with open(EVIDENCE_PATH, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"\nSaved evidence to {EVIDENCE_PATH}")
        print(f"Summary: {evidence['summary']['passed']}/{evidence['summary']['total']} checks passed.")

        if not all_passed:
            print("ERROR: One or more assertions failed!", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
