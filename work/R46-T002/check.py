#!/usr/bin/env python3
"""
R46-T002: Automated checks for EIFGENs pattern matching in Global/EiffelStudio.gitignore.

Tests that the bare name pattern  EIFGENs  (no leading slash, no trailing slash)
matches the directory at any depth, but does not match names that merely start
with or contain the string "EIFGENs".

The temporary repository is created fresh each run so the checks are
self-contained and do not modify the shared project checkout.
"""

import os
import subprocess
import sys
import tempfile
import shutil

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

failures = []


def run(cmd, cwd=None, check=False):
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=check
    )


def check_ignore(path, cwd, use_index=False):
    """
    Run  git check-ignore -v [--no-index]  on *path* relative to *cwd*.

    Returns:
        (is_ignored: bool, rule: str | None)
        rule is the raw output line, e.g. ".gitignore:2:EIFGENs\tEIFGENs"
    """
    cmd = ["git", "check-ignore", "-v"]
    if not use_index:
        cmd.append("--no-index")
    cmd.append(path)
    result = run(cmd, cwd=cwd)
    ignored = result.returncode == 0
    rule = result.stdout.strip() if ignored else None
    return ignored, rule


def assert_ignored(label, path, cwd, expected_pattern, expected_line):
    ignored, rule = check_ignore(path, cwd)
    ok = True
    if not ignored:
        ok = False
        msg = f"  Expected IGNORED but got NOT_IGNORED for: {path}"
    else:
        # rule format: "<file>:<lineno>:<pattern>\t<path>"
        parts = rule.split("\t")[0].split(":")
        actual_line = int(parts[1]) if len(parts) >= 2 else -1
        actual_pattern = parts[2] if len(parts) >= 3 else ""
        if actual_pattern != expected_pattern:
            ok = False
            msg = f"  Pattern mismatch for {path}: got '{actual_pattern}', want '{expected_pattern}'"
        elif actual_line != expected_line:
            ok = False
            msg = f"  Line mismatch for {path}: got {actual_line}, want {expected_line}"
        else:
            msg = f"  Rule: {rule}"
    status = PASS if ok else FAIL
    print(f"[{status}] {label}")
    print(msg)
    if not ok:
        failures.append(label)


def assert_not_ignored(label, path, cwd):
    ignored, _ = check_ignore(path, cwd)
    ok = not ignored
    status = PASS if ok else FAIL
    print(f"[{status}] {label}")
    if not ok:
        print(f"  Expected NOT_IGNORED but was IGNORED: {path}")
        failures.append(label)


def assert_tracked_not_hidden(label, path, cwd):
    """Verify git check-ignore (with index) returns exit 1 for a tracked file."""
    ignored, rule = check_ignore(path, cwd, use_index=True)
    # Tracked files must NOT be reported as ignored by the index-aware check
    ok = not ignored
    status = PASS if ok else FAIL
    print(f"[{status}] {label}")
    if not ok:
        print(f"  Tracked file incorrectly reported as ignored: {path}  rule={rule}")
        failures.append(label)
    else:
        print(f"  Tracked file correctly not hidden by .gitignore (index-aware check)")


def assert_tracked_visible_in_ls_files(label, path, cwd):
    """Verify the file is in git's index (i.e. it is tracked)."""
    result = run(["git", "ls-files", path], cwd=cwd)
    ok = path in result.stdout
    status = PASS if ok else FAIL
    print(f"[{status}] {label}")
    if not ok:
        print(f"  File not found in git index: {path}")
        failures.append(label)
    else:
        print(f"  File is tracked: {result.stdout.strip()}")


# ---------------------------------------------------------------------------
# Build temporary repository
# ---------------------------------------------------------------------------

def build_temp_repo():
    tmpdir = tempfile.mkdtemp(prefix="eiffelstudio-r46t002-")

    r = run(["git", "init", tmpdir])
    assert r.returncode == 0, f"git init failed: {r.stderr}"
    run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
    run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)

    # Write the EiffelStudio .gitignore (line 1 = comment, line 2 = EIFGENs)
    with open(os.path.join(tmpdir, ".gitignore"), "w") as f:
        f.write("# The compilation directory\n")
        f.write("EIFGENs\n")

    # Fixture 1: EIFGENs at repository root
    os.makedirs(os.path.join(tmpdir, "EIFGENs"), exist_ok=True)
    open(os.path.join(tmpdir, "EIFGENs", "W_code"), "w").close()

    # Fixture 2: EIFGENs one level deep
    os.makedirs(os.path.join(tmpdir, "project", "EIFGENs"), exist_ok=True)
    open(os.path.join(tmpdir, "project", "EIFGENs", "W_code"), "w").close()

    # Fixture 3: EIFGENs two levels deep
    os.makedirs(os.path.join(tmpdir, "deep", "nested", "EIFGENs"), exist_ok=True)
    open(os.path.join(tmpdir, "deep", "nested", "EIFGENs", "W_code"), "w").close()

    # Fixture 4: EIFGENs-backup  (should NOT match)
    os.makedirs(os.path.join(tmpdir, "EIFGENs-backup"), exist_ok=True)
    open(os.path.join(tmpdir, "EIFGENs-backup", "notes.txt"), "w").close()

    # Fixture 5: EIFGENs_extra  (should NOT match)
    os.makedirs(os.path.join(tmpdir, "EIFGENs_extra"), exist_ok=True)
    open(os.path.join(tmpdir, "EIFGENs_extra", "notes.txt"), "w").close()

    # Fixture 6: EIGENS  (misspelling, should NOT match)
    os.makedirs(os.path.join(tmpdir, "EIGENS"), exist_ok=True)
    open(os.path.join(tmpdir, "EIGENS", "notes.txt"), "w").close()

    # Fixture 7: legitimate source files
    open(os.path.join(tmpdir, "main.e"), "w").close()
    open(os.path.join(tmpdir, "config.ecf"), "w").close()
    open(os.path.join(tmpdir, "README.md"), "w").close()

    # Tracked file inside EIFGENs (force-added)
    # project/EIFGENs already exists from fixture 2
    with open(os.path.join(tmpdir, "project", "EIFGENs", "tracked.e"), "w") as f:
        f.write("-- tracked source file\n")
    run(["git", "add", "-f", "project/EIFGENs/tracked.e"], cwd=tmpdir, check=True)
    run(
        ["git", "commit", "-m", "Track file inside EIFGENs for tracked-file test"],
        cwd=tmpdir, check=True,
    )

    return tmpdir


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("R46-T002: EIFGENs pattern matching checks")
    print("=" * 60)

    tmpdir = build_temp_repo()
    print(f"Temporary repo: {tmpdir}\n")

    try:
        # --- Ignored paths ---
        print("── Paths that SHOULD be ignored ──────────────────────────")
        assert_ignored(
            "Root-level EIFGENs directory",
            "EIFGENs", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )
        assert_ignored(
            "File inside root-level EIFGENs",
            "EIFGENs/W_code", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )
        assert_ignored(
            "EIFGENs one level deep (project/EIFGENs)",
            "project/EIFGENs", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )
        assert_ignored(
            "File inside one-level-deep EIFGENs",
            "project/EIFGENs/W_code", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )
        assert_ignored(
            "EIFGENs two levels deep (deep/nested/EIFGENs)",
            "deep/nested/EIFGENs", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )
        assert_ignored(
            "File inside two-level-deep EIFGENs",
            "deep/nested/EIFGENs/W_code", tmpdir,
            expected_pattern="EIFGENs", expected_line=2,
        )

        print()
        # --- Not ignored paths ---
        print("── Paths that should NOT be ignored ──────────────────────")
        assert_not_ignored(
            "EIFGENs-backup directory (suffix added)",
            "EIFGENs-backup", tmpdir,
        )
        assert_not_ignored(
            "File inside EIFGENs-backup",
            "EIFGENs-backup/notes.txt", tmpdir,
        )
        assert_not_ignored(
            "EIFGENs_extra directory (suffix added)",
            "EIFGENs_extra", tmpdir,
        )
        assert_not_ignored(
            "File inside EIFGENs_extra",
            "EIFGENs_extra/notes.txt", tmpdir,
        )
        assert_not_ignored(
            "EIGENS directory (misspelling)",
            "EIGENS", tmpdir,
        )
        assert_not_ignored(
            "File inside EIGENS",
            "EIGENS/notes.txt", tmpdir,
        )
        assert_not_ignored("Eiffel source file (main.e)", "main.e", tmpdir)
        assert_not_ignored("Eiffel config file (config.ecf)", "config.ecf", tmpdir)
        assert_not_ignored("README.md", "README.md", tmpdir)

        print()
        # --- Tracked-file behaviour ---
        print("── Tracked-file behaviour ────────────────────────────────")
        assert_tracked_visible_in_ls_files(
            "Tracked file inside EIFGENs appears in git index",
            "project/EIFGENs/tracked.e", tmpdir,
        )
        assert_tracked_not_hidden(
            "Tracked file inside EIFGENs not hidden by index-aware gitignore check",
            "project/EIFGENs/tracked.e", tmpdir,
        )
        # --no-index check still reports the pattern (documents the behaviour)
        ignored, rule = check_ignore("project/EIFGENs/tracked.e", tmpdir, use_index=False)
        label = "git check-ignore --no-index still reports pattern for tracked path"
        ok = ignored and rule is not None
        print(f"[{PASS if ok else FAIL}] {label}")
        if ok:
            print(f"  Rule: {rule}")
        else:
            print(f"  Unexpected: ignored={ignored}, rule={rule}")
            if not ok:
                failures.append(label)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

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
