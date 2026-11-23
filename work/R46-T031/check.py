#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import tempfile
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "Gradle.gitignore"
EVIDENCE = pathlib.Path(__file__).resolve().parent

def run(command, cwd, check=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {command}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result

def write_file(repo, relative, content="fixture\n"):
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def ignored(repo, relative):
    result = run(
        ["git", "check-ignore", "-q", "--no-index", relative],
        repo,
        check=False,
    )
    return result.returncode == 0

def matching_rule(repo, relative):
    result = run(
        ["git", "check-ignore", "-v", "--no-index", relative],
        repo,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def main():
    assert TEMPLATE.exists(), f"Missing template: {TEMPLATE}"

    template_text = TEMPLATE.read_text()
    required_rules = [
        ".gradle",
        "**/build/",
        "!**/src/**/build/",
    ]

    for rule in required_rules:
        assert rule in template_text, f"Missing expected rule: {rule}"

    results = []

    with tempfile.TemporaryDirectory(prefix="gradle-ignore-test-") as temp:
        repo = pathlib.Path(temp)

        run(["git", "init"], repo)
        run(["git", "config", "user.name", "Task Checker"], repo)
        run(["git", "config", "user.email", "checker@example.test"], repo)

        # Prove that a file tracked before ignore rules are added
        # remains tracked even when the rule would ignore it.
        write_file(repo, "build/tracked-output.txt", "tracked before ignore\n")
        run(["git", "add", "build/tracked-output.txt"], repo)
        run(["git", "commit", "-m", "Add tracked build fixture"], repo)

        (repo / ".gitignore").write_text(template_text)

        # Positive and negative fixtures for .gradle
        write_file(repo, ".gradle/cache.bin")
        write_file(repo, "module/.gradle/cache.bin")
        write_file(repo, "gradle-cache/cache.bin")

        # Positive and negative fixtures for build/
        write_file(repo, "build/output.txt")
        write_file(repo, "module/build/output.txt")
        write_file(repo, "build.gradle")
        write_file(repo, "build.gradle.kts")

        # Negation: build directories inside source trees should remain visible.
        write_file(repo, "src/main/java/build/legitimate-source.txt")
        write_file(repo, "module/src/test/build/legitimate-test-output.txt")

        cases = [
            (".gradle/cache.bin", True, ".gradle"),
            ("module/.gradle/cache.bin", True, ".gradle"),
            ("gradle-cache/cache.bin", False, None),
            ("build/output.txt", True, "**/build/"),
            ("module/build/output.txt", True, "**/build/"),
            ("build.gradle", False, None),
            ("build.gradle.kts", False, None),
            ("src/main/java/build/legitimate-source.txt", False, None),
            ("module/src/test/build/legitimate-test-output.txt", False, None),
        ]

        for path, expected_ignored, expected_rule in cases:
            actual_ignored = ignored(repo, path)
            assert actual_ignored == expected_ignored, (
                f"{path}: expected ignored={expected_ignored}, "
                f"got ignored={actual_ignored}"
            )

            rule_output = matching_rule(repo, path)

            if expected_ignored:
                assert rule_output is not None, (
                    f"{path} should have a matching ignore rule"
                )
                assert expected_rule in rule_output, (
                    f"{path}: expected responsible rule {expected_rule}, "
                    f"got {rule_output}"
                )

            results.append({
                "path": path,
                "expected_ignored": expected_ignored,
                "actual_ignored": actual_ignored,
                "expected_rule": expected_rule,
                "actual_rule_output": rule_output,
                "passed": True,
            })

        # Modify a file that was tracked before .gitignore was applied.
        tracked = repo / "build/tracked-output.txt"
        tracked.write_text("modified tracked file\n")

        status = run(["git", "status", "--porcelain"], repo).stdout
        assert "build/tracked-output.txt" in status, (
            "Tracked build fixture should remain visible in git status "
            "after being modified, despite the ignore rule"
        )

        report = {
            "task": "R46-T031",
            "template": "Gradle.gitignore",
            "timestamp": datetime.now().isoformat(),
            "git_version": run(["git", "--version"], repo).stdout.strip(),
            "python_version": os.sys.version,
            "rules_tested": required_rules,
            "fixtures": results,
            "tracked_file_behavior": {
                "path": "build/tracked-output.txt",
                "modified_after_ignore_added": True,
                "visible_in_git_status": True,
                "status_output": status.strip(),
                "passed": True,
            },
            "overall_pass": True,
        }

        report_path = EVIDENCE / "results.json"
        report_path.write_text(json.dumps(report, indent=2))

        print("PASS: All Gradle.gitignore fixture checks passed.")
        print(f"Evidence written to: {report_path}")
        print(f"Git version: {report['git_version']}")
        print(f"Fixtures checked: {len(results)}")

if __name__ == "__main__":
    main()
