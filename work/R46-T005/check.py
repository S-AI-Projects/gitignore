#!/usr/bin/env python3
"""
R46-T005: Automated checks for ModelSim.gitignore patterns.

Verifies:
  - [_@]* matches any file/directory starting with _ or @.
  - *.mti matches ModelSim Transcript Index files.
  - *.dat matches simulation data files.
  - Near-miss names are NOT matched.
  - Tracked-file behaviour: a file committed before .gitignore is applied
    remains tracked despite matching an ignore rule.

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


def assert_tracked_visible(label, path, cwd):
    """Assert a tracked file remains visible (not hidden) after .gitignore added."""
    # git status --porcelain shows tracked files; a modified/clean tracked
    # file will NOT appear as '??' or '!!' — it appears as ' M' or nothing.
    # We check that git ls-files still lists it.
    result = run(["git", "ls-files", path], cwd=cwd)
    ok = path in result.stdout
    report(label, ok,
           f"File is still tracked (in index)." if ok
           else f"Expected tracked, but not in index: {path!r}")


def touch(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELSIM_GITIGNORE = (PROJECT_ROOT / "ModelSim.gitignore").read_text()


def test_positive_patterns():
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="modelsim-t005-pos-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(MODELSIM_GITIGNORE)

    try:
        # [_@]* — files starting with _
        touch(f"{tmp}/_transcript")
        assert_ignored("_transcript ignored by [_@]*", "_transcript", tmp, "[_@]*")

        # [_@]* — files starting with @
        touch(f"{tmp}/@log")
        assert_ignored("@log ignored by [_@]*", "@log", tmp, "[_@]*")

        # *.mti — ModelSim Transcript Index
        touch(f"{tmp}/sim.mti")
        assert_ignored("sim.mti ignored by *.mti", "sim.mti", tmp, "*.mti")

        # *.dat — simulation data
        touch(f"{tmp}/results.dat")
        assert_ignored("results.dat ignored by *.dat", "results.dat", tmp, "*.dat")

        # Nested *.dat
        touch(f"{tmp}/subdir/wave.dat")
        assert_ignored("subdir/wave.dat ignored by *.dat", "subdir/wave.dat", tmp, "*.dat")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negative_patterns():
    print("── Negative (near-miss) pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="modelsim-t005-neg-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(MODELSIM_GITIGNORE)

    try:
        # regular filename — not starting with _ or @, not matching any other rule
        touch(f"{tmp}/design.vhd")
        assert_not_ignored("design.vhd is NOT ignored (Verilog/VHDL source file)",
                           "design.vhd", tmp)

        # testbench.sv — source file; should not be ignored
        touch(f"{tmp}/testbench.sv")
        assert_not_ignored("testbench.sv is NOT ignored (SystemVerilog source)",
                           "testbench.sv", tmp)

        # README.txt — documentation file; not matching any ModelSim rule
        touch(f"{tmp}/README.txt")
        assert_not_ignored("README.txt is NOT ignored (documentation)",
                           "README.txt", tmp)

        # .mti extension requires dot-prefix; without it no match
        touch(f"{tmp}/simulationmti")
        assert_not_ignored("simulationmti is NOT ignored (no .mti extension)",
                           "simulationmti", tmp)

        # .dat extension with other prefix; .datx is not .dat
        touch(f"{tmp}/results.datx")
        assert_not_ignored("results.datx is NOT ignored (not *.dat)",
                           "results.datx", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tracked_file_behaviour():
    """
    Task type: Tracked-file behavior.
    Demonstrate that a file committed before .gitignore is applied
    remains tracked and visible despite now matching an ignore rule.
    """
    print("── Tracked-file behaviour ──")
    tmp = tempfile.mkdtemp(prefix="modelsim-t005-tracked-")
    git_init(tmp)

    # 1. Commit a matching file BEFORE the .gitignore
    touch(f"{tmp}/_tracked_work_file")
    result = run(["git", "add", "_tracked_work_file"], cwd=tmp)
    report("Pre-gitignore _tracked_work_file staged", result.returncode == 0)
    result = run(["git", "commit", "-m", "track _tracked_work_file before gitignore"],
                 cwd=tmp)
    report("Pre-gitignore _tracked_work_file committed", result.returncode == 0)

    # 2. Now add the .gitignore
    (Path(tmp) / ".gitignore").write_text(MODELSIM_GITIGNORE)
    result = run(["git", "add", ".gitignore"], cwd=tmp)
    result = run(["git", "commit", "-m", "add ModelSim .gitignore"], cwd=tmp)
    report("ModelSim .gitignore committed", result.returncode == 0)

    try:
        # 3. Verify the file is STILL tracked despite the [_@]* rule
        assert_tracked_visible(
            "Previously-tracked _tracked_work_file remains in index",
            "_tracked_work_file", tmp
        )

        # 4. git check-ignore (with index) returns exit 1 for tracked file
        ignored, raw = check_ignore("_tracked_work_file", tmp, use_index=True)
        report(
            "git check-ignore (index mode) returns non-ignored for tracked file",
            not ignored,
            "Correctly shows tracked file not ignored." if not ignored
            else f"Unexpected: {raw}"
        )

        # 5. git check-ignore --no-index still identifies the matching rule
        ignored_ni, raw_ni = check_ignore("_tracked_work_file", tmp, use_index=False)
        report(
            "--no-index identifies [_@]* pattern for tracked file",
            ignored_ni and "[_@]*" in raw_ni,
            f"Rule: {raw_ni}" if ignored_ni and "[_@]*" in raw_ni
            else f"Got: {raw_ni!r}"
        )

        # 6. An untracked matching file IS hidden
        touch(f"{tmp}/_new_untracked")
        ignored_new, _ = check_ignore("_new_untracked", tmp)
        report(
            "New untracked _new_untracked IS ignored by [_@]*",
            ignored_new
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T005: ModelSim.gitignore pattern checks")
    print("=" * 60)
    print()

    test_positive_patterns()
    print()

    test_negative_patterns()
    print()

    test_tracked_file_behaviour()
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
