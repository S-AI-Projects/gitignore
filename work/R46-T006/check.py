#!/usr/bin/env python3
"""
R46-T006: Automated checks for Modelica.gitignore patterns.

Verifies:
  - *~ matches editor backup files ending in ~.
  - *.bak matches general backup files.
  - *.bak-mo matches Modelica-specific backup files.
  - Space-containing paths are correctly handled.
  - Case behaviour on this filesystem is recorded.
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
MODELICA_GITIGNORE = (PROJECT_ROOT / "Modelica.gitignore").read_text()


def test_positive_patterns():
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="modelica-t006-pos-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(MODELICA_GITIGNORE)

    try:
        # *~ — editor backup (vim, emacs, etc.)
        touch(f"{tmp}/model.mo~")
        assert_ignored("model.mo~ ignored by *~", "model.mo~", tmp, "*~")

        # *~ — file ending in ~ with space in name
        touch(f"{tmp}/my model.mo~")
        assert_ignored("'my model.mo~' (space in name) ignored by *~",
                       "my model.mo~", tmp, "*~")

        # *.bak — general backup
        touch(f"{tmp}/model.bak")
        assert_ignored("model.bak ignored by *.bak", "model.bak", tmp, "*.bak")

        # *.bak — with space in path
        touch(f"{tmp}/sub dir/component.bak")
        assert_ignored("'sub dir/component.bak' ignored by *.bak",
                       "sub dir/component.bak", tmp, "*.bak")

        # *.bak-mo — Modelica-specific backup
        touch(f"{tmp}/model.bak-mo")
        assert_ignored("model.bak-mo ignored by *.bak-mo", "model.bak-mo", tmp, "*.bak-mo")

        # *.bak-mo in nested directory
        touch(f"{tmp}/subpackage/component.bak-mo")
        assert_ignored("subpackage/component.bak-mo ignored by *.bak-mo",
                       "subpackage/component.bak-mo", tmp, "*.bak-mo")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negative_patterns():
    print("── Negative (near-miss) pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="modelica-t006-neg-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(MODELICA_GITIGNORE)

    try:
        # .mo source file — should NOT be ignored
        touch(f"{tmp}/model.mo")
        assert_not_ignored("model.mo is NOT ignored (Modelica source file)",
                           "model.mo", tmp)

        # .package file — not matching any pattern
        touch(f"{tmp}/package.order")
        assert_not_ignored("package.order is NOT ignored", "package.order", tmp)

        # .bak without dot — should not match *.bak
        touch(f"{tmp}/modelbak")
        assert_not_ignored("modelbak is NOT ignored (no .bak extension)",
                           "modelbak", tmp)

        # .bak-mo without dot — should not match *.bak-mo
        touch(f"{tmp}/modelbak-mo")
        assert_not_ignored("modelbak-mo is NOT ignored (no .bak-mo extension)",
                           "modelbak-mo", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_case_behaviour():
    """
    Record filesystem case behaviour and core.ignorecase setting.
    On macOS the default filesystem is case-insensitive (HFS+/APFS),
    so core.ignorecase defaults to true. On Linux it defaults to false.
    """
    print("── Case behaviour ──")
    tmp = tempfile.mkdtemp(prefix="modelica-t006-case-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(MODELICA_GITIGNORE)

    try:
        # Record the actual core.ignorecase setting
        result = run(["git", "config", "--get", "core.ignorecase"], cwd=tmp)
        ignorecase = result.stdout.strip()
        print(f"       core.ignorecase = {ignorecase!r}")

        # On case-insensitive filesystem: MODEL.BAK would also match *.bak
        # We test the lower-case canonical form which must always match
        touch(f"{tmp}/model.bak")
        ignored, raw = check_ignore("model.bak", tmp)
        report("model.bak (canonical case) is ignored", ignored,
               f"Rule: {raw}" if ignored else "Expected IGNORED")

        # Case variant test — record result without asserting (filesystem-dependent)
        touch(f"{tmp}/MODEL.BAK")
        ignored_upper, raw_upper = check_ignore("MODEL.BAK", tmp)
        print(f"[INFO] MODEL.BAK ignored={ignored_upper} "
              f"(core.ignorecase={ignorecase}; filesystem-dependent)")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T006: Modelica.gitignore pattern checks")
    print("=" * 60)
    print()

    test_positive_patterns()
    print()

    test_negative_patterns()
    print()

    test_case_behaviour()
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
