#!/usr/bin/env python3
"""
R46-T009: Automated checks for Global/Otto.gitignore patterns.

Verifies:
  - .otto/ (trailing slash) matches the .otto directory but NOT a file named .otto.
  - Compares: original .otto/ rule vs broader .otto rule vs narrower /.otto/ rule.
  - Shows false positive (broader .otto matches file named .otto).
  - Shows false negative (narrower /.otto/ only matches root .otto/).
  - Near-miss names are NOT matched by the original .otto/ rule.

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


def assert_ignored(label, path, cwd, expected_pattern):
    ignored, raw = check_ignore(path, cwd)
    if not ignored:
        report(label, False, f"Expected IGNORED, got NOT_IGNORED: {path!r}")
        return
    _, pattern = parse_rule(raw)
    ok = pattern == expected_pattern
    report(label, ok,
           f"Rule: {raw}" if ok
           else f"Expected pattern={expected_pattern!r}, got pattern={pattern!r}")


def assert_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd)
    report(label, not ignored,
           "" if not ignored
           else f"Expected NOT_IGNORED, got IGNORED: {path!r} {raw}")


def touch(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OTTO_GITIGNORE = (PROJECT_ROOT / "Global" / "Otto.gitignore").read_text()


def test_original_rule():
    """Test the original .otto/ rule (trailing slash = directories only)."""
    print("── Original rule: .otto/ ──")
    tmp = tempfile.mkdtemp(prefix="otto-t009-orig-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(OTTO_GITIGNORE)

    try:
        # .otto/ as a directory — should be IGNORED
        Path(f"{tmp}/.otto").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            ".otto/ directory is IGNORED by .otto/",
            ".otto", tmp,
            ".otto/"
        )

        # File inside .otto/ — transitively ignored
        touch(f"{tmp}/.otto/compiled.json")
        assert_ignored(
            ".otto/compiled.json is IGNORED (inside ignored directory)",
            ".otto/compiled.json", tmp,
            ".otto/"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_file_named_otto():
    """
    .otto/ (trailing slash) does NOT match a regular file named .otto.
    This is the key directory-vs-file distinction.
    """
    print("── File named .otto: NOT matched by .otto/ ──")
    tmp = tempfile.mkdtemp(prefix="otto-t009-file-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(OTTO_GITIGNORE)

    try:
        # A regular file named .otto should NOT be ignored
        touch(f"{tmp}/.otto")
        assert_not_ignored(
            "file named .otto is NOT ignored by .otto/ (trailing slash = dirs only)",
            ".otto", tmp
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_broader_rule_false_positive():
    """
    Broader alternative: .otto (without trailing slash).
    FALSE POSITIVE: matches a plain file named .otto that should not be ignored.
    """
    print("── Broader alternative: .otto (no trailing slash) — false positive ──")
    tmp = tempfile.mkdtemp(prefix="otto-t009-broad-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(".otto\n")

    try:
        # Directory .otto — still ignored
        Path(f"{tmp}/.otto").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            ".otto directory is IGNORED by broader .otto rule",
            ".otto", tmp,
            ".otto"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # Separate repo: file named .otto (false positive)
    tmp2 = tempfile.mkdtemp(prefix="otto-t009-broad-fp-")
    git_init(tmp2)
    (Path(tmp2) / ".gitignore").write_text(".otto\n")

    try:
        touch(f"{tmp2}/.otto")
        ignored, raw = check_ignore(".otto", tmp2)
        # This IS ignored by the broader rule — a false positive
        report(
            "FALSE POSITIVE: file .otto is IGNORED by broader .otto rule (should not be ignored)",
            ignored,  # We EXPECT this to be True (a false positive)
            f"Rule: {raw}" if ignored else "Unexpected: not ignored by broader rule"
        )

    finally:
        shutil.rmtree(tmp2, ignore_errors=True)


def test_narrower_rule_false_negative():
    """
    Narrower alternative: /.otto/ (leading slash anchors to repository root).
    FALSE NEGATIVE: nested .otto/ directories are NOT matched.
    """
    print("── Narrower alternative: /.otto/ (anchored) — false negative ──")
    tmp = tempfile.mkdtemp(prefix="otto-t009-narrow-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text("/.otto/\n")

    try:
        # Root .otto/ — still ignored
        Path(f"{tmp}/.otto").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            ".otto/ at root IS ignored by narrower /.otto/ rule",
            ".otto", tmp,
            "/.otto/"
        )

        # Nested .otto/ inside a subdirectory — FALSE NEGATIVE
        Path(f"{tmp}/subproject/.otto").mkdir(parents=True, exist_ok=True)
        ignored, raw = check_ignore("subproject/.otto", tmp)
        # With /.otto/ the nested subproject/.otto is NOT ignored — false negative
        report(
            "FALSE NEGATIVE: subproject/.otto is NOT ignored by /.otto/ (anchored rule misses nested dirs)",
            not ignored,
            "" if not ignored else f"Unexpected: ignored by {raw}"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_near_miss():
    """Near-miss names that should NOT be matched by the original .otto/ rule."""
    print("── Near-miss pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="otto-t009-miss-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(OTTO_GITIGNORE)

    try:
        # .otto_backup directory — not matched
        Path(f"{tmp}/.otto_backup").mkdir(parents=True, exist_ok=True)
        assert_not_ignored(
            ".otto_backup/ directory is NOT ignored",
            ".otto_backup", tmp
        )

        # otto/ (no dot prefix) — not matched
        Path(f"{tmp}/otto").mkdir(parents=True, exist_ok=True)
        assert_not_ignored(
            "otto/ directory is NOT ignored (no leading dot)",
            "otto", tmp
        )

        # README.md — not matched
        touch(f"{tmp}/README.md")
        assert_not_ignored(
            "README.md is NOT ignored",
            "README.md", tmp
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T009: Global/Otto.gitignore pattern checks")
    print("=" * 60)
    print()

    test_original_rule()
    print()

    test_file_named_otto()
    print()

    test_broader_rule_false_positive()
    print()

    test_narrower_rule_false_negative()
    print()

    test_near_miss()
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
