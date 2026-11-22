#!/usr/bin/env python3
"""
R46-T010: Automated checks for Global/Dreamweaver.gitignore patterns.

Verifies:
  - _notes matches the _notes directory (or file) added by Dreamweaver for notes.
  - _compareTemp matches the _compareTemp directory for file comparison temp data.
  - configs/ matches the configs directory (trailing slash = directories only).
  - Marks ignored outputs and tracked inputs with the matching rule and line number.
  - Near-miss names are NOT matched.

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
DW_GITIGNORE = (PROJECT_ROOT / "Global" / "Dreamweaver.gitignore").read_text()


def test_positive_patterns():
    """
    Test _notes, _compareTemp, configs/ match their intended targets.
    Documents a small project tree using this template.
    """
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="dw-t010-pos-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(DW_GITIGNORE)

    try:
        # _notes — Dreamweaver local notes directory
        Path(f"{tmp}/_notes").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            "_notes directory is IGNORED by _notes",
            "_notes", tmp,
            "_notes"
        )

        # _notes contents — transitively ignored
        touch(f"{tmp}/_notes/site-plan.txt")
        assert_ignored(
            "_notes/site-plan.txt is IGNORED (inside ignored _notes)",
            "_notes/site-plan.txt", tmp,
            "_notes"
        )

        # _compareTemp — Dreamweaver file comparison temporary data
        Path(f"{tmp}/_compareTemp").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            "_compareTemp directory is IGNORED by _compareTemp",
            "_compareTemp", tmp,
            "_compareTemp"
        )

        # _compareTemp contents
        touch(f"{tmp}/_compareTemp/index.html.tmp")
        assert_ignored(
            "_compareTemp/index.html.tmp is IGNORED (inside ignored _compareTemp)",
            "_compareTemp/index.html.tmp", tmp,
            "_compareTemp"
        )

        # configs/ — Dreamweaver site configuration directory (trailing slash)
        Path(f"{tmp}/configs").mkdir(parents=True, exist_ok=True)
        assert_ignored(
            "configs/ directory is IGNORED by configs/",
            "configs", tmp,
            "configs/"
        )

        # configs/ contents
        touch(f"{tmp}/configs/site.xml")
        assert_ignored(
            "configs/site.xml is IGNORED (inside ignored configs/)",
            "configs/site.xml", tmp,
            "configs/"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_configs_dirs_only():
    """
    configs/ (trailing slash) matches directories only.
    A file named 'configs' would NOT be ignored.
    """
    print("── configs/ trailing slash: directories only ──")
    tmp = tempfile.mkdtemp(prefix="dw-t010-cfgdir-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(DW_GITIGNORE)

    try:
        # A regular file named 'configs' should NOT be ignored
        touch(f"{tmp}/configs")
        assert_not_ignored(
            "file named 'configs' is NOT ignored by configs/ (trailing slash = dirs only)",
            "configs", tmp
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tracked_inputs():
    """
    Documents tracked (source) inputs that should remain visible despite the template.
    These are files in a typical Dreamweaver web project that must NOT be ignored.
    """
    print("── Tracked inputs: should NOT be ignored ──")
    tmp = tempfile.mkdtemp(prefix="dw-t010-tracked-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(DW_GITIGNORE)

    try:
        # HTML source — primary web page files
        touch(f"{tmp}/index.html")
        assert_not_ignored("index.html is NOT ignored (source file)", "index.html", tmp)

        # CSS — stylesheet
        touch(f"{tmp}/styles/main.css")
        assert_not_ignored("styles/main.css is NOT ignored (stylesheet)", "styles/main.css", tmp)

        # JavaScript — script file
        touch(f"{tmp}/scripts/app.js")
        assert_not_ignored("scripts/app.js is NOT ignored (script)", "scripts/app.js", tmp)

        # Images — web assets
        touch(f"{tmp}/images/logo.png")
        assert_not_ignored("images/logo.png is NOT ignored (image)", "images/logo.png", tmp)

        # README
        touch(f"{tmp}/README.md")
        assert_not_ignored("README.md is NOT ignored (documentation)", "README.md", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_near_miss():
    """Near-miss names that should NOT be matched."""
    print("── Near-miss pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="dw-t010-miss-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(DW_GITIGNORE)

    try:
        # notes (no leading underscore) — should NOT be ignored
        Path(f"{tmp}/notes").mkdir(parents=True, exist_ok=True)
        assert_not_ignored(
            "notes/ directory is NOT ignored (no leading underscore)", "notes", tmp
        )

        # _notes_backup — should NOT be ignored
        Path(f"{tmp}/_notes_backup").mkdir(parents=True, exist_ok=True)
        assert_not_ignored(
            "_notes_backup/ is NOT ignored (extra suffix)", "_notes_backup", tmp
        )

        # compareTemp (no leading underscore) — should NOT be ignored
        Path(f"{tmp}/compareTemp").mkdir(parents=True, exist_ok=True)
        assert_not_ignored(
            "compareTemp/ is NOT ignored (no leading underscore)", "compareTemp", tmp
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T010: Global/Dreamweaver.gitignore pattern checks")
    print("=" * 60)
    print()

    test_positive_patterns()
    print()

    test_configs_dirs_only()
    print()

    test_tracked_inputs()
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
