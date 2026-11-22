#!/usr/bin/env python3
"""
R46-T008: Automated checks for CodeIgniter.gitignore patterns.

Verifies:
  - */config/development is ignored (config dir).
  - */logs/log-*.php is ignored (log files).
  - !*/logs/index.html is NOT ignored (negation rule preserves index.html).
  - Near-miss names are NOT matched.
  - Negation last-match behavior is correctly demonstrated.

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


def is_effectively_ignored(path, cwd):
    """
    Returns True if the path is EFFECTIVELY ignored (not re-included by negation).
    Uses git status --porcelain: untracked (??) means not ignored.
    git check-ignore --no-index can report exit 0 for negation rules, which is
    misleading. We use git status as the authoritative check.
    """
    result = run(["git", "status", "--porcelain", path], cwd=cwd)
    # ?? = untracked (not ignored), nothing = ignored or not present
    output = result.stdout.strip()
    # Create the file first if needed; we're calling this after touch()
    return "??" not in output and output != ""


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
    """
    Asserts a path is NOT effectively ignored.
    Uses git status --porcelain: '?? <path>' means not ignored (untracked).
    git check-ignore --no-index can report exit 0 for negation rules; we
    use git status as the authoritative source.
    """
    result = run(["git", "status", "--porcelain", path], cwd=cwd)
    output = result.stdout.strip()
    is_untracked = output.startswith("??")
    report(label, is_untracked,
           "" if is_untracked
           else f"Expected NOT_IGNORED (??), got: {output!r}")


def touch(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODEIGNITER_GITIGNORE = (PROJECT_ROOT / "CodeIgniter.gitignore").read_text()


def test_positive_patterns():
    """
    */config/development is ignored.
    */logs/log-*.php matches log files in any */logs/ directory.
    For the path application/logs/log-*.php, the CI3 rule application/logs/*
    (line 15) also matches and is later in the file, so git reports it as the
    responsible rule. Both rules produce IGNORED for log-*.php files.
    application/logs/* (CI3) overrides */logs/log-*.php for the CI3 path.
    """
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="codeigniter-t008-pos-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(CODEIGNITER_GITIGNORE)

    try:
        # */config/development — CodeIgniter development config directory
        Path(f"{tmp}/application/config/development").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            "application/config/development ignored by */config/development",
            "application/config/development", tmp,
            "*/config/development"
        )

        # */logs/log-*.php — log file in a non-CI3 logs path (no application/logs/* override)
        # Use a different prefix so application/logs/* does not apply
        touch(f"{tmp}/myapp/logs/log-2024-01-15.php")
        assert_ignored(
            "myapp/logs/log-2024-01-15.php ignored by */logs/log-*.php",
            "myapp/logs/log-2024-01-15.php", tmp,
            "*/logs/log-*.php"
        )

        touch(f"{tmp}/myapp/logs/log-2024-12-01.php")
        assert_ignored(
            "myapp/logs/log-2024-12-01.php ignored by */logs/log-*.php",
            "myapp/logs/log-2024-12-01.php", tmp,
            "*/logs/log-*.php"
        )

        # CodeIgniter 3: application/logs/* — all logs
        touch(f"{tmp}/application/logs/error.log")
        assert_ignored(
            "application/logs/error.log ignored by application/logs/*",
            "application/logs/error.log", tmp,
            "application/logs/*"
        )

        # application/logs/log-*.php — also ignored, but by CI3 application/logs/*
        # (later rule wins; demonstrates last-match ordering)
        touch(f"{tmp}/application/logs/log-2024-01-15.php")
        ignored, raw = check_ignore("application/logs/log-2024-01-15.php", tmp)
        report(
            "application/logs/log-2024-01-15.php is IGNORED (by application/logs/* or */logs/log-*.php)",
            ignored,
            f"Rule: {raw}" if ignored else "Unexpected: not ignored"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negation_index_html():
    """
    !*/logs/index.html — negation preserves index.html in logs directories.
    For the path application/logs/index.html, the CI3 rule
    !application/logs/index.html (line 16) is a negation that re-includes it.
    git check-ignore --no-index still reports the last matching rule, which is
    the negation rule itself; the file is NOT effectively ignored.

    We use a non-CI3 logs path to test !*/logs/index.html directly.
    """
    print("── Negation rule check: !*/logs/index.html ──")
    tmp = tempfile.mkdtemp(prefix="codeigniter-t008-neg-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(CODEIGNITER_GITIGNORE)

    try:
        # index.html in a non-CI3 logs path: not matched by application/logs/*
        # so the negation !*/logs/index.html is the controlling rule
        touch(f"{tmp}/myapp/logs/index.html")
        assert_not_ignored(
            "myapp/logs/index.html is NOT ignored (!*/logs/index.html negation)",
            "myapp/logs/index.html", tmp
        )

        # index.html in CI3 application/logs/: !application/logs/index.html negation
        touch(f"{tmp}/application/logs/index.html")
        assert_not_ignored(
            "application/logs/index.html is NOT ignored (!application/logs/index.html)",
            "application/logs/index.html", tmp
        )

        # A different .html file in application/logs/ should still be ignored
        touch(f"{tmp}/application/logs/other.html")
        assert_ignored(
            "application/logs/other.html is ignored by application/logs/*",
            "application/logs/other.html", tmp,
            "application/logs/*"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negative_patterns():
    print("── Negative (near-miss) pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="codeigniter-t008-miss-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(CODEIGNITER_GITIGNORE)

    try:
        # Production config should NOT be ignored
        touch(f"{tmp}/application/config/production/database.php")
        assert_not_ignored(
            "application/config/production/database.php is NOT ignored",
            "application/config/production/database.php", tmp
        )

        # Non-PHP log files in logs/ should be ignored by application/logs/*
        # but NOT by */logs/log-*.php
        touch(f"{tmp}/application/logs/app.log")
        assert_ignored(
            "application/logs/app.log is ignored (by application/logs/*)",
            "application/logs/app.log", tmp,
            "application/logs/*"
        )

        # Source PHP files outside logs should NOT be ignored
        touch(f"{tmp}/application/controllers/Welcome.php")
        assert_not_ignored(
            "application/controllers/Welcome.php is NOT ignored (source file)",
            "application/controllers/Welcome.php", tmp
        )

        # README.md should NOT be ignored
        touch(f"{tmp}/README.md")
        assert_not_ignored(
            "README.md is NOT ignored",
            "README.md", tmp
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T008: CodeIgniter.gitignore pattern checks")
    print("=" * 60)
    print()

    test_positive_patterns()
    print()

    test_negation_index_html()
    print()

    test_negative_patterns()
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
