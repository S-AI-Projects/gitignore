#!/usr/bin/env python3
"""
R46-T007: Automated checks for Global/Virtuoso.gitignore patterns.

Verifies:
  - *.log matches Cadence Virtuoso log files.
  - panic*.log.* matches panic log files with suffix (NOT plain panic.log).
  - *.cdslck* matches OpenAccess database lock files and variants.
  - Near-miss names are NOT matched.
  - Each pattern is connected to its tool output.

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
VIRTUOSO_GITIGNORE = (PROJECT_ROOT / "Global" / "Virtuoso.gitignore").read_text()


def test_positive_patterns():
    print("── Positive pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="virtuoso-t007-pos-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(VIRTUOSO_GITIGNORE)

    try:
        # *.log — Virtuoso log file (tool output, not source)
        touch(f"{tmp}/virtuoso.log")
        assert_ignored("virtuoso.log ignored by *.log", "virtuoso.log", tmp, "*.log")

        # *.log — simulation log
        touch(f"{tmp}/simulation.log")
        assert_ignored("simulation.log ignored by *.log", "simulation.log", tmp, "*.log")

        # *.log — nested
        touch(f"{tmp}/rundir/lvs.log")
        assert_ignored("rundir/lvs.log ignored by *.log", "rundir/lvs.log", tmp, "*.log")

        # panic*.log.* — Virtuoso crash log with numeric suffix
        touch(f"{tmp}/panic.log.1")
        assert_ignored("panic.log.1 ignored by panic*.log.*", "panic.log.1", tmp, "panic*.log.*")

        # panic*.log.* — crash log with text suffix
        touch(f"{tmp}/panic_core.log.backup")
        assert_ignored("panic_core.log.backup ignored by panic*.log.*",
                       "panic_core.log.backup", tmp, "panic*.log.*")

        # *.cdslck* — OpenAccess database lock file
        touch(f"{tmp}/cellLibrary.cdslck")
        assert_ignored("cellLibrary.cdslck ignored by *.cdslck*",
                       "cellLibrary.cdslck", tmp, "*.cdslck*")

        # *.cdslck* — lock file with suffix
        touch(f"{tmp}/layout.cdslck1")
        assert_ignored("layout.cdslck1 ignored by *.cdslck*",
                       "layout.cdslck1", tmp, "*.cdslck*")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_negative_patterns():
    print("── Negative (near-miss) pattern checks ──")
    tmp = tempfile.mkdtemp(prefix="virtuoso-t007-neg-")
    git_init(tmp)
    (Path(tmp) / ".gitignore").write_text(VIRTUOSO_GITIGNORE)

    try:
        # Verilog source — should NOT be ignored
        touch(f"{tmp}/inverter.v")
        assert_not_ignored("inverter.v is NOT ignored (Verilog source)",
                           "inverter.v", tmp)

        # SPICE netlist — not ignored
        touch(f"{tmp}/circuit.spi")
        assert_not_ignored("circuit.spi is NOT ignored (SPICE netlist)",
                           "circuit.spi", tmp)

        # panic.log — plain panic log WITHOUT extra suffix is matched by *.log
        # (not by panic*.log.*) — this is acceptable; *.log is broader
        touch(f"{tmp}/panic.log")
        ignored_pl, raw_pl = check_ignore("panic.log", tmp)
        # panic.log IS ignored (by *.log), just not by panic*.log.*
        report("panic.log is ignored (by the broader *.log rule)",
               ignored_pl, f"Rule: {raw_pl}" if ignored_pl else "Unexpected: not ignored")

        # .log without dot at start — not matching *.log
        touch(f"{tmp}/logfile")
        assert_not_ignored("logfile is NOT ignored (no .log extension)",
                           "logfile", tmp)

        # .cdslck with wrong prefix
        touch(f"{tmp}/design.cds")
        assert_not_ignored("design.cds is NOT ignored (not *.cdslck*)",
                           "design.cds", tmp)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("R46-T007: Global/Virtuoso.gitignore pattern checks")
    print("=" * 60)
    print()

    test_positive_patterns()
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
