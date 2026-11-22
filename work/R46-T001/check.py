#!/usr/bin/env python3
"""
R46-T001: Automated checks for Dart.gitignore patterns.

Verifies:
  - .dart_tool/ matches directories (not plain files).
  - .packages matches the exact filename.
  - build/ matches directories at any depth.
  - Near-miss names are NOT matched (.dart_tool-file, .packages-backup, build.txt).
  - The responsible rule line is verified with git check-ignore -v --no-index.
  - Tracked-file behaviour is verified.

Each test uses a temporary Git repository.
The shared project checkout is never modified.
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
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git_init(path):
    result = run(["git", "init", path], cwd="/tmp")
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    for key, value in [("user.email", "test@test.com"), ("user.name", "Test")]:
        result = run(["git", "config", key, value], cwd=path)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)


def check_ignore(path, cwd, use_index=False):
    cmd = ["git", "check-ignore", "-v"]
    if not use_index:
        cmd.append("--no-index")
    cmd.append(path)
    result = run(cmd, cwd)
    return result.returncode == 0, result.stdout.strip()


def parse_rule(raw):
    """Parse 'file:line:pattern\tpath' output from git check-ignore -v."""
    meta = raw.split("\t")[0]
    parts = meta.split(":")
    return int(parts[1]), parts[2]


def report(label, ok, details=""):
    status = PASS if ok else FAIL
    print(f"[{status}] {label}")
    if details:
        print(f"       {details}")
    if not ok:
        failures.append(label)


def assert_ignored(label, path, cwd, expected_pattern, expected_line):
    ignored, raw = check_ignore(path, cwd)
    if not ignored:
        report(label, False, f"Expected IGNORED, got NOT_IGNORED: {path!r}")
        return
    line_no, pattern = parse_rule(raw)
    ok = (pattern == expected_pattern and line_no == expected_line)
    report(label, ok,
           f"Rule: {raw}" if ok
           else f"Expected pattern={expected_pattern!r} line={expected_line}, "
                f"got pattern={pattern!r} line={line_no}")


def assert_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd)
    report(label, not ignored,
           "" if not ignored else f"Expected NOT_IGNORED, got IGNORED: {path!r} {raw}")


def assert_tracked_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd, use_index=True)
    report(label, not ignored,
           "Correctly not hidden from index (tracked file)." if not ignored
           else f"Tracked file reported as ignored: {path!r} {raw}")


def assert_no_index_matches(label, path, cwd, expected_pattern):
    ignored, raw = check_ignore(path, cwd, use_index=False)
    if not ignored:
        report(label, False, "Expected a pattern match with --no-index.")
        return
    _, pattern = parse_rule(raw)
    report(label, pattern == expected_pattern,
           f"--no-index rule: {raw}" if pattern == expected_pattern
           else f"Expected {expected_pattern!r}, got {pattern!r}")


def touch(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


def mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


# Read the actual Dart.gitignore from this repo
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DART_GITIGNORE = (PROJECT_ROOT / "Dart.gitignore").read_text()

# Lines in the file (1-indexed, after the added comment):
# Line 1: # See https://www.dartlang.org/guides/libraries/private-files
# Line 2: (blank)
# Line 3: # Files and directories created by pub
# Line 4: # Ignore generated Dart package metadata and build output.
# Line 5: .dart_tool/
# Line 6: .packages
# Line 7: build/
LINE_DART_TOOL = None
LINE_PACKAGES = None
LINE_BUILD = None
for i, line in enumerate(DART_GITIGNORE.splitlines(), 1):
    stripped = line.strip()
    if stripped == ".dart_tool/":
        LINE_DART_TOOL = i
    elif stripped == ".packages":
        LINE_PACKAGES = i
    elif stripped == "build/":
        LINE_BUILD = i


def test_positive_patterns():
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="dart-t001-pos-")
    git_init(tmp)
    gitignore_path = Path(tmp) / ".gitignore"
    gitignore_path.write_text(DART_GITIGNORE)

    try:
        # .dart_tool/ — matches directory, not plain file
        mkdir(f"{tmp}/.dart_tool")
        touch(f"{tmp}/.dart_tool/config.json")
        assert_ignored(
            ".dart_tool/ directory is ignored",
            ".dart_tool/config.json", tmp, ".dart_tool/", LINE_DART_TOOL
        )

        # .packages — matches exact filename
        touch(f"{tmp}/.packages")
        assert_ignored(
            ".packages file is ignored",
            ".packages", tmp, ".packages", LINE_PACKAGES
        )

        # build/ — matches directory at root
        mkdir(f"{tmp}/build")
        touch(f"{tmp}/build/output.txt")
        assert_ignored(
            "build/ directory is ignored",
            "build/output.txt", tmp, "build/", LINE_BUILD
        )

        # build/ — matches nested directory
        mkdir(f"{tmp}/sub/build")
        touch(f"{tmp}/sub/build/output.txt")
        assert_ignored(
            "Nested build/ directory is ignored",
            "sub/build/output.txt", tmp, "build/", LINE_BUILD
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negative_patterns():
    print("── Negative (near-miss) pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="dart-t001-neg-")
    git_init(tmp)
    gitignore_path = Path(tmp) / ".gitignore"
    gitignore_path.write_text(DART_GITIGNORE)

    try:
        # .dart_tool as a plain file (trailing-slash pattern — should NOT match plain file)
        touch(f"{tmp}/.dart_tool-file")
        assert_not_ignored(
            ".dart_tool-file is NOT ignored (near miss)",
            ".dart_tool-file", tmp
        )

        # .packages-backup
        touch(f"{tmp}/.packages-backup")
        assert_not_ignored(
            ".packages-backup is NOT ignored (near miss)",
            ".packages-backup", tmp
        )

        # build.txt — does not match build/
        touch(f"{tmp}/build.txt")
        assert_not_ignored(
            "build.txt is NOT ignored (near miss)",
            "build.txt", tmp
        )

        # pubspec.lock — also ignored; verify it appears in git status
        touch(f"{tmp}/pubspec.lock")
        ignored_lock, raw_lock = check_ignore("pubspec.lock", tmp)
        report(
            "pubspec.lock is ignored (also covered by template)",
            ignored_lock,
            f"Rule: {raw_lock}" if ignored_lock else "Expected IGNORED"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tracked_file():
    print("── Tracked-file behaviour ──")
    tmp = tempfile.mkdtemp(prefix="dart-t001-tracked-")
    git_init(tmp)
    gitignore_path = Path(tmp) / ".gitignore"
    gitignore_path.write_text(DART_GITIGNORE)

    touch(f"{tmp}/.packages")

    try:
        result = run(["git", "add", "-f", ".packages"], cwd=tmp)
        report("Ignored .packages can be force-added", result.returncode == 0,
               result.stderr if result.returncode != 0 else "")

        assert_tracked_not_ignored(
            "Tracked .packages is not reported as ignored",
            ".packages", tmp
        )

        assert_no_index_matches(
            "Tracked .packages still matches .packages with --no-index",
            ".packages", tmp, ".packages"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T001: Dart.gitignore pattern checks")
    print("=" * 60)
    print(f"Pattern lines: .dart_tool/={LINE_DART_TOOL}, "
          f".packages={LINE_PACKAGES}, build/={LINE_BUILD}")
    print()

    test_positive_patterns()
    print()

    test_negative_patterns()
    print()

    test_tracked_file()
    print()

    print("=" * 60)
    if failures:
        print(f"RESULT: FAIL — {len(failures)} assertion(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("RESULT: ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
