
#!/usr/bin/env python3
"""
R46-T002: Automated checks for EIFGENs pattern matching
using the actual Global/EiffelStudio.gitignore template.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
failures = []


def run(cmd, cwd=None):
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True
    )


def check_ignore(path, cwd, use_index=False):
    cmd = ["git", "check-ignore", "-v"]

    if not use_index:
        cmd.append("--no-index")

    cmd.append(path)
    result = run(cmd, cwd)

    return result.returncode == 0, result.stdout.strip()


def report(label, ok, details=""):
    print(f"[{PASS if ok else FAIL}] {label}")

    if details:
        print(f"  {details}")

    if not ok:
        failures.append(label)


def assert_ignored(label, path, cwd):
    ignored, rule = check_ignore(path, cwd)
    ok = False
    details = ""

    if ignored and rule:
        parts = rule.split("\t")[0].split(":")
        actual_line = int(parts[1]) if len(parts) >= 2 else -1
        actual_pattern = parts[2] if len(parts) >= 3 else ""

        ok = actual_pattern == "EIFGENs" and actual_line == 7

        details = (
            f"Rule: {rule}" if ok
            else f"Got pattern={actual_pattern}, line={actual_line}; "
                 "expected EIFGENs at line 7"
        )
    else:
        details = f"Expected ignored, but was not ignored: {path}"

    report(label, ok, details)


def assert_not_ignored(label, path, cwd):
    ignored, _ = check_ignore(path, cwd)

    report(
        label,
        not ignored,
        "" if not ignored else f"Unexpectedly ignored: {path}"
    )


def build_temp_repo():
    tmpdir = tempfile.mkdtemp(prefix="eiffelstudio-r46t002-")

    repo_root = Path(__file__).resolve().parents[2]
    template = repo_root / "Global" / "EiffelStudio.gitignore"

    if not template.is_file():
        raise FileNotFoundError(f"Template not found: {template}")

    result = run(["git", "init", tmpdir])

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    for key, value in [
        ("user.email", "test@test.com"),
        ("user.name", "Test"),
    ]:
        result = run(["git", "config", key, value], tmpdir)

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

    # Copy the actual project template.
    shutil.copyfile(template, Path(tmpdir) / ".gitignore")

    # Positive fixtures.
    for directory in [
        "EIFGENs",
        "project/EIFGENs",
        "deep/nested/EIFGENs",
    ]:
        path = Path(tmpdir) / directory
        path.mkdir(parents=True, exist_ok=True)
        (path / "W_code").write_text("test\n")

    # Negative fixtures.
    for directory in [
        "EIFGENs-backup",
        "EIFGENs_extra",
        "EIGENS",
    ]:
        path = Path(tmpdir) / directory
        path.mkdir(parents=True, exist_ok=True)
        (path / "notes.txt").write_text("test\n")

    # Legitimate files.
    for filename in ["main.e", "config.ecf", "README.md"]:
        (Path(tmpdir) / filename).write_text("test\n")

    # Force-add and commit a file inside EIFGENs.
    tracked = Path(tmpdir) / "project/EIFGENs/tracked.e"
    tracked.write_text("-- tracked source file\n")

    result = run(
        ["git", "add", "-f", "project/EIFGENs/tracked.e"],
        tmpdir
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    result = run(
        ["git", "commit", "-m", "Track EIFGENs test file"],
        tmpdir
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return tmpdir


def main():
    tmpdir = None

    try:
        print("=" * 60)
        print("R46-T002: EIFGENs pattern matching checks")
        print("=" * 60)

        tmpdir = build_temp_repo()
        print(f"Temporary repo: {tmpdir}\n")

        print("── Paths that SHOULD be ignored ──────────────────────────")

        positive = [
            ("Root-level EIFGENs directory", "EIFGENs"),
            ("File inside root-level EIFGENs", "EIFGENs/W_code"),
            ("EIFGENs one level deep", "project/EIFGENs"),
            ("File inside one-level-deep EIFGENs",
             "project/EIFGENs/W_code"),
            ("EIFGENs two levels deep", "deep/nested/EIFGENs"),
            ("File inside two-level-deep EIFGENs",
             "deep/nested/EIFGENs/W_code"),
        ]

        for label, path in positive:
            assert_ignored(label, path, tmpdir)

        print("\n── Paths that should NOT be ignored ──────────────────────")

        negative = [
            ("EIFGENs-backup directory", "EIFGENs-backup"),
            ("File inside EIFGENs-backup", "EIFGENs-backup/notes.txt"),
            ("EIFGENs_extra directory", "EIFGENs_extra"),
            ("File inside EIFGENs_extra", "EIFGENs_extra/notes.txt"),
            ("EIGENS directory (misspelling)", "EIGENS"),
            ("File inside EIGENS", "EIGENS/notes.txt"),
            ("Eiffel source file", "main.e"),
            ("Eiffel config file", "config.ecf"),
            ("README.md", "README.md"),
        ]

        for label, path in negative:
            assert_not_ignored(label, path, tmpdir)

        print("\n── Tracked-file behaviour ────────────────────────────────")

        tracked_path = "project/EIFGENs/tracked.e"

        result = run(
            ["git", "ls-files", "--error-unmatch", tracked_path],
            tmpdir
        )

        report(
            "Tracked file inside EIFGENs appears in git index",
            result.returncode == 0,
            result.stdout.strip() or result.stderr.strip()
        )

        ignored, rule = check_ignore(
            tracked_path, tmpdir, use_index=True
        )

        report(
            "Tracked file is not reported as ignored (index-aware)",
            not ignored,
            "Correctly not reported as ignored"
            if not ignored else f"Unexpected ignore rule: {rule}"
        )

        ignored, rule = check_ignore(
            tracked_path, tmpdir, use_index=False
        )

        report(
            "git check-ignore --no-index still reports the pattern",
            ignored and "EIFGENs" in rule,
            rule or "Expected the EIFGENs rule to match"
        )

        status = run(
            ["git", "status", "--porcelain", "--", tracked_path],
            tmpdir
        )

        report(
            "git status --porcelain shows tracked file as clean",
            status.returncode == 0 and status.stdout.strip() == "",
            status.stdout.strip() or "No changes: tracked file is clean"
        )

    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)

    if failures:
        print(f"RESULT: FAIL — {len(failures)} check(s) failed")

        for failure in failures:
            print(f"  - {failure}")

        print("=" * 60)
        sys.exit(1)

    print("RESULT: ALL 19 CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
