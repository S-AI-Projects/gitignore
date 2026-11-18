#!/usr/bin/env python3
"""
R46-T004: Automated checks for Lilypond.gitignore patterns.

Verifies *.pdf, *.ps, and *.midi pattern behaviour:
  - Files with matching extensions are ignored.
  - Directories with matching extensions are ignored (bare glob, no trailing slash).
  - Files inside ignored directories are ignored transitively.
  - Non-matching names are not ignored.
  - The exact responsible rule and line number are verified for every ignored path.
  - Trailing-slash variant (*.pdf/) is compared against the bare (*.pdf) rule.
  - Tracked-file behaviour is verified.

Each run builds and tears down its own temporary Git repository.
The shared project checkout is never modified.
"""

import os
import shutil
import subprocess
import sys
import tempfile

# ── colour helpers ────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SECTION = "\033[94m{}\033[0m"

failures: list[str] = []


# ── subprocess helpers ────────────────────────────────────────────────────────

def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git_init(path):
    run(["git", "init", path], cwd="/tmp")
    run(["git", "config", "user.email", "test@test.com"], cwd=path)
    run(["git", "config", "user.name", "Test"], cwd=path)


def check_ignore(path, cwd, use_index=False):
    """
    Returns (is_ignored: bool, raw_rule: str | None).
    raw_rule format: "<file>:<line>:<pattern>\\t<path>"
    """
    cmd = ["git", "check-ignore", "-v"]
    if not use_index:
        cmd.append("--no-index")
    cmd.append(path)
    r = run(cmd, cwd=cwd)
    ignored = r.returncode == 0
    return ignored, (r.stdout.strip() if ignored else None)


def parse_rule(raw):
    """Return (line_no: int, pattern: str) from a raw check-ignore output line."""
    # format: ".gitignore:<line>:<pattern>\t<path>"
    meta = raw.split("\t")[0]           # ".gitignore:2:*.ps"
    parts = meta.split(":")             # [".gitignore", "2", "*.ps"]
    return int(parts[1]), parts[2]


# ── assertion helpers ─────────────────────────────────────────────────────────

def assert_ignored(label, path, cwd, expected_pattern, expected_line):
    ignored, raw = check_ignore(path, cwd)
    if not ignored:
        print(f"[{FAIL}] {label}")
        print(f"       Expected IGNORED, got NOT_IGNORED: {path}")
        failures.append(label)
        return
    line_no, pattern = parse_rule(raw)
    ok = (pattern == expected_pattern) and (line_no == expected_line)
    print(f"[{PASS if ok else FAIL}] {label}")
    if ok:
        print(f"       Rule: {raw}")
    else:
        print(f"       Expected pattern={expected_pattern!r} line={expected_line}, "
              f"got pattern={pattern!r} line={line_no}")
        failures.append(label)


def assert_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd)
    ok = not ignored
    print(f"[{PASS if ok else FAIL}] {label}")
    if not ok:
        print(f"       Expected NOT_IGNORED, got IGNORED: {path}  rule={raw}")
        failures.append(label)


def assert_tracked_not_ignored(label, path, cwd):
    """Index-aware check must NOT report a tracked file as ignored."""
    ignored, raw = check_ignore(path, cwd, use_index=True)
    ok = not ignored
    print(f"[{PASS if ok else FAIL}] {label}")
    if ok:
        print(f"       Correctly not hidden from index (tracked file).")
    else:
        print(f"       Tracked file incorrectly reported as ignored: {path}  rule={raw}")
        failures.append(label)


def assert_no_index_matches(label, path, cwd, expected_pattern):
    """--no-index check MUST still report the pattern for a tracked file."""
    ignored, raw = check_ignore(path, cwd, use_index=False)
    if not ignored:
        print(f"[{FAIL}] {label}")
        print(f"       Expected pattern match with --no-index, got NOT_IGNORED: {path}")
        failures.append(label)
        return
    _, pattern = parse_rule(raw)
    ok = pattern == expected_pattern
    print(f"[{PASS if ok else FAIL}] {label}")
    if ok:
        print(f"       --no-index rule: {raw}")
    else:
        print(f"       Expected pattern {expected_pattern!r}, got {pattern!r}")
        failures.append(label)


# ── build helpers ─────────────────────────────────────────────────────────────

def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    open(path, "w").close()


def mkdir(path):
    os.makedirs(path, exist_ok=True)


LILYPOND_GITIGNORE = (
    "# Compiled output files (PDF, PostScript, MIDI).\n"              # line 1
    "# These bare glob patterns match both files and directories of the same\n"  # line 2
    "# extension at any depth in the repository tree. Files inside a matched\n"  # line 3
    "# directory are ignored transitively. Names that only start with or contain\n"  # line 4
    "# the extension string (e.g. score.pdf.bak) are not matched.\n"  # line 5
    "*.pdf\n"   # line 6
    "*.ps\n"    # line 7
    "*.midi\n"  # line 8
    "*.mid\n"   # line 9
    "*.log\n"   # line 10
    "*~\n"      # line 11
)


# ── main test suites ──────────────────────────────────────────────────────────

def test_bare_patterns():
    """Core checks: *.pdf (line 1), *.ps (line 2), *.midi (line 3)."""
    tmp = tempfile.mkdtemp(prefix="lilypond-t004-bare-")
    git_init(tmp)
    with open(os.path.join(tmp, ".gitignore"), "w") as f:
        f.write(LILYPOND_GITIGNORE)
    try:
        # ── *.pdf ────────────────────────────────────────────────────────────
        touch(os.path.join(tmp, "score.pdf"))
        mkdir(os.path.join(tmp, "docs.pdf"))
        touch(os.path.join(tmp, "docs.pdf", "notes.ly"))
        mkdir(os.path.join(tmp, "build", "output.pdf"))
        touch(os.path.join(tmp, "build", "output.pdf", "source.ly"))

        # ── *.ps ─────────────────────────────────────────────────────────────
        touch(os.path.join(tmp, "render.ps"))
        mkdir(os.path.join(tmp, "engraving.ps"))
        touch(os.path.join(tmp, "engraving.ps", "tune.ly"))

        # ── *.midi ───────────────────────────────────────────────────────────
        touch(os.path.join(tmp, "song.midi"))
        mkdir(os.path.join(tmp, "orchestral.midi"))
        touch(os.path.join(tmp, "orchestral.midi", "part.ly"))

        # ── non-matching ─────────────────────────────────────────────────────
        touch(os.path.join(tmp, "score.ly"))
        touch(os.path.join(tmp, "score.pdf.bak"))
        touch(os.path.join(tmp, "score.pdff"))
        touch(os.path.join(tmp, "render.ps.orig"))
        touch(os.path.join(tmp, "README.md"))

        # ── assertions ───────────────────────────────────────────────────────
        print(SECTION.format("── *.pdf (line 6) ──────────────────────────────────"))
        assert_ignored("*.pdf: file score.pdf", "score.pdf", tmp, "*.pdf", 6)
        assert_ignored("*.pdf: dir  docs.pdf", "docs.pdf", tmp, "*.pdf", 6)
        assert_ignored("*.pdf: .ly inside docs.pdf dir", "docs.pdf/notes.ly", tmp, "*.pdf", 6)
        assert_ignored("*.pdf: nested dir build/output.pdf", "build/output.pdf", tmp, "*.pdf", 6)
        assert_ignored("*.pdf: .ly inside nested dir", "build/output.pdf/source.ly", tmp, "*.pdf", 6)
        assert_not_ignored("*.pdf: score.pdf.bak not ignored", "score.pdf.bak", tmp)
        assert_not_ignored("*.pdf: score.pdff not ignored", "score.pdff", tmp)

        print()
        print(SECTION.format("── *.ps (line 7) ───────────────────────────────────"))
        assert_ignored("*.ps: file render.ps", "render.ps", tmp, "*.ps", 7)
        assert_ignored("*.ps: dir  engraving.ps", "engraving.ps", tmp, "*.ps", 7)
        assert_ignored("*.ps: .ly inside engraving.ps dir", "engraving.ps/tune.ly", tmp, "*.ps", 7)
        assert_not_ignored("*.ps: render.ps.orig not ignored", "render.ps.orig", tmp)

        print()
        print(SECTION.format("── *.midi (line 8) ─────────────────────────────────"))
        assert_ignored("*.midi: file song.midi", "song.midi", tmp, "*.midi", 8)
        assert_ignored("*.midi: dir  orchestral.midi", "orchestral.midi", tmp, "*.midi", 8)
        assert_ignored("*.midi: .ly inside orchestral.midi dir", "orchestral.midi/part.ly", tmp, "*.midi", 8)

        print()
        print(SECTION.format("── Non-matching files ──────────────────────────────"))
        assert_not_ignored("score.ly not ignored", "score.ly", tmp)
        assert_not_ignored("README.md not ignored", "README.md", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_trailing_slash_comparison():
    """
    Compare  *.pdf  (matches files AND directories)
    versus   *.pdf/ (matches directories ONLY).

    The original Lilypond.gitignore uses the bare form (*.pdf).
    This test documents the difference and confirms the original rule
    is intentionally broad (matches both files and dirs).
    """
    print(SECTION.format("── Trailing-slash comparison: *.pdf vs *.pdf/ ──────"))

    def build(rule):
        tmp = tempfile.mkdtemp(prefix="lilypond-trailing-")
        git_init(tmp)
        with open(os.path.join(tmp, ".gitignore"), "w") as f:
            f.write(rule + "\n")
        touch(os.path.join(tmp, "score.pdf"))
        mkdir(os.path.join(tmp, "docs.pdf"))
        touch(os.path.join(tmp, "docs.pdf", "notes.ly"))
        return tmp

    bare = build("*.pdf")
    slash = build("*.pdf/")
    try:
        # Bare rule ignores both
        assert_ignored("bare *.pdf: file score.pdf IGNORED", "score.pdf", bare, "*.pdf", 1)
        assert_ignored("bare *.pdf: dir  docs.pdf IGNORED", "docs.pdf", bare, "*.pdf", 1)

        # Trailing-slash rule ignores only the directory
        assert_not_ignored("*.pdf/: file score.pdf NOT ignored", "score.pdf", slash)
        assert_ignored("*.pdf/: dir  docs.pdf IGNORED", "docs.pdf", slash, "*.pdf/", 1)
        assert_ignored("*.pdf/: .ly inside docs.pdf IGNORED", "docs.pdf/notes.ly", slash, "*.pdf/", 1)

    finally:
        shutil.rmtree(bare, ignore_errors=True)
        shutil.rmtree(slash, ignore_errors=True)


def test_tracked_file():
    """Tracked files are not hidden by gitignore (index-aware check)."""
    print(SECTION.format("── Tracked-file behaviour ──────────────────────────"))
    tmp = tempfile.mkdtemp(prefix="lilypond-tracked-")
    git_init(tmp)
    with open(os.path.join(tmp, ".gitignore"), "w") as f:
        f.write(LILYPOND_GITIGNORE)
    touch(os.path.join(tmp, "score.pdf"))
    # Force-add and commit
    run(["git", "add", "-f", "score.pdf"], cwd=tmp)
    run(["git", "commit", "-m", "track score.pdf"], cwd=tmp)
    try:
        # ls-files confirms it is tracked
        r = run(["git", "ls-files", "score.pdf"], cwd=tmp)
        ok = "score.pdf" in r.stdout
        print(f"[{PASS if ok else FAIL}] Tracked: score.pdf in git index")
        if not ok:
            failures.append("Tracked: score.pdf in git index")

        assert_tracked_not_ignored(
            "Tracked score.pdf: index-aware check exits 1 (not ignored)",
            "score.pdf", tmp,
        )
        assert_no_index_matches(
            "Tracked score.pdf: --no-index still reports *.pdf rule",
            "score.pdf", tmp, "*.pdf",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("R46-T004: Lilypond.gitignore pattern checks")
    print("=" * 60)
    print()

    test_bare_patterns()
    print()
    test_trailing_slash_comparison()
    print()
    test_tracked_file()

    print()
    print("=" * 60)
    if failures:
        print(f"RESULT: FAIL — {len(failures)} assertion(s) failed:")
        for f in failures:
            print(f"  • {f}")
        sys.exit(1)
    else:
        print("RESULT: ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
