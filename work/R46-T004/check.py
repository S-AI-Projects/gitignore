
#!/usr/bin/env python3
"""
R46-T004: Automated checks for Lilypond.gitignore patterns.

Verifies:
  - *.pdf, *.ps, and *.midi match files and directories.
  - Files inside ignored directories are ignored.
  - Non-matching names are not ignored.
  - The responsible rule and line number are verified.
  - Trailing-slash behaviour is compared.
  - Same basename file/directory fixtures are tested in separate repos.
  - Tracked-file behaviour is verified.

Each test uses temporary Git repositories.
The shared project checkout is never modified.
"""

import os
import shutil
import subprocess
import sys
import tempfile

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SECTION = "\033[94m{}\033[0m"

failures = []


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git_init(path):
    result = run(["git", "init", path], cwd="/tmp")
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    for key, value in [
        ("user.email", "test@test.com"),
        ("user.name", "Test"),
    ]:
        result = run(["git", "config", key, value], cwd=path)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)


def check_ignore(path, cwd, use_index=False):
    cmd = ["git", "check-ignore", "-v"]
    if not use_index:
        cmd.append("--no-index")
    cmd.append(path)

    result = run(cmd, cwd=cwd)
    ignored = result.returncode == 0
    return ignored, result.stdout.strip() if ignored else None


def parse_rule(raw):
    meta = raw.split("\t")[0]
    parts = meta.split(":")
    return int(parts[1]), parts[2]


def assert_ignored(label, path, cwd, expected_pattern, expected_line):
    ignored, raw = check_ignore(path, cwd)

    if not ignored:
        print(f"[{FAIL}] {label}")
        print(f"       Expected IGNORED, got NOT_IGNORED: {path}")
        failures.append(label)
        return

    line_no, pattern = parse_rule(raw)
    ok = pattern == expected_pattern and line_no == expected_line

    print(f"[{PASS if ok else FAIL}] {label}")

    if ok:
        print(f"       Rule: {raw}")
    else:
        print(
            f"       Expected pattern={expected_pattern!r} "
            f"line={expected_line}, got pattern={pattern!r} "
            f"line={line_no}"
        )
        failures.append(label)


def assert_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd)
    ok = not ignored

    print(f"[{PASS if ok else FAIL}] {label}")

    if not ok:
        print(f"       Expected NOT_IGNORED, got IGNORED: {path} {raw}")
        failures.append(label)


def assert_tracked_not_ignored(label, path, cwd):
    ignored, raw = check_ignore(path, cwd, use_index=True)
    ok = not ignored

    print(f"[{PASS if ok else FAIL}] {label}")

    if ok:
        print("       Correctly not hidden from index (tracked file).")
    else:
        print(f"       Tracked file reported as ignored: {path} {raw}")
        failures.append(label)


def assert_no_index_matches(label, path, cwd, expected_pattern):
    ignored, raw = check_ignore(path, cwd, use_index=False)

    if not ignored:
        print(f"[{FAIL}] {label}")
        print("       Expected a pattern match with --no-index.")
        failures.append(label)
        return

    _, pattern = parse_rule(raw)
    ok = pattern == expected_pattern

    print(f"[{PASS if ok else FAIL}] {label}")

    if ok:
        print(f"       --no-index rule: {raw}")
    else:
        print(f"       Expected {expected_pattern!r}, got {pattern!r}")
        failures.append(label)


def touch(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w") as file:
        file.close()


def mkdir(path):
    os.makedirs(path, exist_ok=True)


LILYPOND_GITIGNORE = (
    "# Compiled output files (PDF, PostScript, MIDI).\n"
    "# These bare glob patterns match both files and directories of the same\n"
    "# extension at any depth in the repository tree. Files inside a matched\n"
    "# directory are ignored transitively. Names that only start with or contain\n"
    "# the extension string (e.g. score.pdf.bak) are not matched.\n"
    "*.pdf\n"
    "*.ps\n"
    "*.midi\n"
    "*.mid\n"
    "*.log\n"
    "*~\n"
)


def write_gitignore(repo, content=LILYPOND_GITIGNORE):
    with open(os.path.join(repo, ".gitignore"), "w") as file:
        file.write(content)


def test_bare_patterns():
    print(SECTION.format("── Bare pattern checks ──"))

    tmp = tempfile.mkdtemp(prefix="lilypond-t004-bare-")
    git_init(tmp)
    write_gitignore(tmp)

    try:
        # PDF fixtures
        touch(os.path.join(tmp, "score.pdf"))
        mkdir(os.path.join(tmp, "docs.pdf"))
        touch(os.path.join(tmp, "docs.pdf", "notes.ly"))
        mkdir(os.path.join(tmp, "build", "output.pdf"))
        touch(os.path.join(tmp, "build", "output.pdf", "source.ly"))

        # PostScript fixtures
        touch(os.path.join(tmp, "render.ps"))
        mkdir(os.path.join(tmp, "engraving.ps"))
        touch(os.path.join(tmp, "engraving.ps", "tune.ly"))

        # MIDI fixtures
        touch(os.path.join(tmp, "song.midi"))
        mkdir(os.path.join(tmp, "orchestral.midi"))
        touch(os.path.join(tmp, "orchestral.midi", "part.ly"))

        # Nonmatching fixtures
        touch(os.path.join(tmp, "score.ly"))
        touch(os.path.join(tmp, "score.pdf.bak"))
        touch(os.path.join(tmp, "score.pdff"))
        touch(os.path.join(tmp, "render.ps.orig"))
        touch(os.path.join(tmp, "README.md"))

        # *.pdf is line 6
        assert_ignored("*.pdf file score.pdf", "score.pdf", tmp, "*.pdf", 6)
        assert_ignored("*.pdf directory docs.pdf", "docs.pdf", tmp, "*.pdf", 6)
        assert_ignored(
            "*.pdf file inside docs.pdf",
            "docs.pdf/notes.ly", tmp, "*.pdf", 6
        )
        assert_ignored(
            "*.pdf nested directory",
            "build/output.pdf", tmp, "*.pdf", 6
        )
        assert_ignored(
            "*.pdf file inside nested directory",
            "build/output.pdf/source.ly", tmp, "*.pdf", 6
        )
        assert_not_ignored("score.pdf.bak not ignored", "score.pdf.bak", tmp)
        assert_not_ignored("score.pdff not ignored", "score.pdff", tmp)

        # *.ps is line 7
        assert_ignored("*.ps file render.ps", "render.ps", tmp, "*.ps", 7)
        assert_ignored("*.ps directory engraving.ps", "engraving.ps", tmp, "*.ps", 7)
        assert_ignored(
            "*.ps file inside engraving.ps",
            "engraving.ps/tune.ly", tmp, "*.ps", 7
        )
        assert_not_ignored("render.ps.orig not ignored", "render.ps.orig", tmp)

        # *.midi is line 8
        assert_ignored("*.midi file song.midi", "song.midi", tmp, "*.midi", 8)
        assert_ignored(
            "*.midi directory orchestral.midi",
            "orchestral.midi", tmp, "*.midi", 8
        )
        assert_ignored(
            "*.midi file inside orchestral.midi",
            "orchestral.midi/part.ly", tmp, "*.midi", 8
        )

        # Other source and documentation files
        assert_not_ignored("score.ly not ignored", "score.ly", tmp)
        assert_not_ignored("README.md not ignored", "README.md", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_trailing_slash_comparison():
    print(SECTION.format("── Trailing-slash comparison ──"))

    def build(rule):
        tmp = tempfile.mkdtemp(prefix="lilypond-trailing-")
        git_init(tmp)
        write_gitignore(tmp, rule + "\n")

        touch(os.path.join(tmp, "score.pdf"))
        mkdir(os.path.join(tmp, "docs.pdf"))
        touch(os.path.join(tmp, "docs.pdf", "notes.ly"))

        return tmp

    bare = build("*.pdf")
    slash = build("*.pdf/")

    try:
        assert_ignored(
            "bare *.pdf matches file",
            "score.pdf", bare, "*.pdf", 1
        )
        assert_ignored(
            "bare *.pdf matches directory",
            "docs.pdf", bare, "*.pdf", 1
        )

        assert_not_ignored(
            "*.pdf/ does not match standalone file",
            "score.pdf", slash
        )
        assert_ignored(
            "*.pdf/ matches directory",
            "docs.pdf", slash, "*.pdf/", 1
        )
        assert_ignored(
            "*.pdf/ ignores contents of directory",
            "docs.pdf/notes.ly", slash, "*.pdf/", 1
        )

    finally:
        shutil.rmtree(bare, ignore_errors=True)
        shutil.rmtree(slash, ignore_errors=True)


def test_same_basename_separate_repos():
    print(SECTION.format("── Same basename in separate repositories ──"))

    file_repo = tempfile.mkdtemp(prefix="lilypond-file-")
    dir_repo = tempfile.mkdtemp(prefix="lilypond-dir-")

    try:
        for repo in (file_repo, dir_repo):
            git_init(repo)
            write_gitignore(repo, "*.pdf\n")

        # Same basename, but in separate repositories.
        touch(os.path.join(file_repo, "same.pdf"))
        mkdir(os.path.join(dir_repo, "same.pdf"))
        touch(os.path.join(dir_repo, "same.pdf", "source.ly"))

        assert_ignored(
            "same.pdf as a file in repository 1",
            "same.pdf", file_repo, "*.pdf", 1
        )
        assert_ignored(
            "same.pdf as a directory in repository 2",
            "same.pdf", dir_repo, "*.pdf", 1
        )
        assert_ignored(
            "source.ly inside same.pdf directory",
            "same.pdf/source.ly", dir_repo, "*.pdf", 1
        )

    finally:
        shutil.rmtree(file_repo, ignore_errors=True)
        shutil.rmtree(dir_repo, ignore_errors=True)


def test_tracked_file():
    print(SECTION.format("── Tracked-file behaviour ──"))

    tmp = tempfile.mkdtemp(prefix="lilypond-tracked-")
    git_init(tmp)
    write_gitignore(tmp)

    touch(os.path.join(tmp, "score.pdf"))

    try:
        result = run(["git", "add", "-f", "score.pdf"], cwd=tmp)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        result = run(["git", "commit", "-m", "track score.pdf"], cwd=tmp)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        tracked = run(["git", "ls-files", "score.pdf"], cwd=tmp)
        ok = "score.pdf" in tracked.stdout

        print(f"[{PASS if ok else FAIL}] score.pdf is tracked")

        if not ok:
            failures.append("score.pdf is tracked")

        assert_tracked_not_ignored(
            "Tracked score.pdf is not reported as ignored",
            "score.pdf", tmp
        )

        assert_no_index_matches(
            "Tracked score.pdf still matches *.pdf with --no-index",
            "score.pdf", tmp, "*.pdf"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T004: Lilypond.gitignore pattern checks")
    print("=" * 60)

    test_bare_patterns()
    print()

    test_trailing_slash_comparison()
    print()

    test_same_basename_separate_repos()
    print()

    test_tracked_file()
    print()

    print("=" * 60)

    if failures:
        print(f"RESULT: FAIL — {len(failures)} assertion(s) failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("RESULT: ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()