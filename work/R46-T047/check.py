#!/usr/bin/env python3
"""Verify PuTTY PPK ignore provenance and source/build fixture behavior."""
import json
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = json.loads((HERE / "fixtures.json").read_text())
TEMPLATE = (ROOT / "Global/PuTTY.gitignore").read_text()


def run(args, cwd, *, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise AssertionError(f"{args!r} failed ({result.returncode}): {result.stderr}")
    return result


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    git_version = run(["git", "--version"], ROOT).stdout.strip()
    python_version = run(["python3", "--version"], ROOT)
    versions = {
        "git": git_version,
        "python": python_version.stdout.strip() or python_version.stderr.strip(),
    }
    actual_fixtures = []
    with tempfile.TemporaryDirectory(prefix="r46-t047-", dir=HERE) as temporary:
        repo = pathlib.Path(temporary)
        run(["git", "init", "-q"], repo)
        tracked = INPUTS["tracked_source"]
        tracked_path = repo / tracked
        tracked_path.parent.mkdir(parents=True, exist_ok=True)
        tracked_path.write_text("// legitimate PPK reader source\n")
        run(["git", "add", "--", tracked], repo)
        identity = ["-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid"]
        run(["git", *identity, "commit", "-qm", "track legitimate source before ignore rule"], repo)

        (repo / ".gitignore").write_text(TEMPLATE)
        run(["git", "add", "--", ".gitignore"], repo)
        run(["git", *identity, "commit", "-qm", "apply PuTTY ignore template"], repo)

        for fixture in INPUTS["fixtures"]:
            path = repo / fixture["path"]
            if fixture["name"] != "source_parser":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"fixture: {fixture['purpose']}\n")
            result = run(
                ["git", "check-ignore", "-v", "--no-index", "--", fixture["path"]],
                repo,
                check=False,
            )
            expect(result.returncode in (0, 1),
                   f"unexpected check-ignore exit {result.returncode} for {fixture['path']}: {result.stderr}")
            ignored = result.returncode == 0
            fields = []
            if ignored:
                source_rule, reported_path = result.stdout.rstrip("\n").split("\t", 1)
                location, pattern = source_rule.rsplit(":", 1)
                source, line_number = location.rsplit(":", 1)
                fields = [source, int(line_number), pattern]
                expect(reported_path == fixture["path"],
                       f"expected reported path {fixture['path']!r}, got {reported_path!r}")
            actual_pattern = fields[2] if fields else None
            actual_line = fields[1] if fields else None
            expect(ignored == fixture["ignored"],
                   f"{fixture['path']}: expected ignored={fixture['ignored']}, got {ignored}")
            expect(actual_pattern == fixture["pattern"],
                   f"{fixture['path']}: expected pattern={fixture['pattern']!r}, got {actual_pattern!r}")
            expect(actual_line == fixture["line"],
                   f"{fixture['path']}: expected line={fixture['line']!r}, got {actual_line!r}")
            actual_fixtures.append({
                "name": fixture["name"],
                "path": fixture["path"],
                "purpose": fixture["purpose"],
                "expected_ignored": fixture["ignored"],
                "actual_ignored": ignored,
                "expected_pattern": fixture["pattern"],
                "actual_pattern": actual_pattern,
                "expected_rule_line": fixture["line"],
                "actual_rule_line": actual_line,
                "git_output": result.stdout.strip(),
            })

        status_before_edit = run(
            ["git", "status", "--porcelain", "--untracked-files=all"], repo
        ).stdout.splitlines()
        expected_untracked = [
            f"?? {fixture['path']}" for fixture in INPUTS["fixtures"]
            if not fixture["ignored"] and fixture["name"] != "source_parser"
        ]
        expect(sorted(status_before_edit) == sorted(expected_untracked),
               f"unexpected status with generated PPK present: {status_before_edit!r}")

        tracked_path.write_text("// edited legitimate PPK reader source\n")
        status_after_edit = run(
            ["git", "status", "--porcelain", "--untracked-files=all"], repo
        ).stdout.splitlines()
        expected_status_after_edit = sorted([f" M {tracked}", *expected_untracked])
        expect(sorted(status_after_edit) == expected_status_after_edit,
               f"expected tracked source edit to remain visible: {status_after_edit!r}")

    output = {
        "tool_versions": versions,
        "template": "Global/PuTTY.gitignore",
        "tested_pattern": "*.ppk",
        "results": actual_fixtures,
        "status_with_new_ignored_key": status_before_edit,
        "expected_status_with_new_ignored_key": expected_untracked,
        "status_after_tracked_source_edit": status_after_edit,
        "expected_status_after_tracked_source_edit": expected_status_after_edit,
    }
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
