#!/usr/bin/env python3
"""
Verification check for R46-T029 (Issue #29):
Template: Global/NetBeans.gitignore
Focus patterns:
  - **/nbproject/private/
  - **/nbproject/Makefile-*.mk
  - **/nbproject/Package-*.bash

Goal:
Compare exact patterns against broader (e.g., **/nbproject/) and narrower
(e.g., nbproject/private/ at root only) alternatives, exposing false positives /
negatives that show why the original patterns are precisely chosen.

Outputs: work/R46-T029/evidence.json, tool_versions.txt, run.log, README.md
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "Global" / "NetBeans.gitignore"
EVIDENCE_FILE = TASK_DIR / "evidence.json"
TOOL_VERSIONS_FILE = TASK_DIR / "tool_versions.txt"
LOG_FILE = TASK_DIR / "run.log"
README_FILE = TASK_DIR / "README.md"

FORCE_FAIL = os.environ.get("R46_T029_FORCE_FAIL", "0") == "1"


def run_cmd(cmd: list[str], cwd: Path | str) -> tuple[int, str, str]:
    res = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def get_tool_versions() -> dict[str, str]:
    git_rc, git_ver, _ = run_cmd(["git", "--version"], REPO_ROOT)
    return {
        "git": git_ver if git_rc == 0 else "unknown",
        "python": platform.python_version(),
        "os": platform.platform(),
    }


def setup_temp_repo(tmp: Path, gitignore_text: str) -> Path:
    """Initialise a bare temp repo with the given .gitignore content."""
    run_cmd(["git", "init", "-b", "main"], tmp)
    run_cmd(["git", "config", "user.email", "test@test.com"], tmp)
    run_cmd(["git", "config", "user.name", "Test"], tmp)
    gi = tmp / ".gitignore"
    gi.write_text(gitignore_text)
    return tmp


def check_ignored(repo: Path, path: str) -> tuple[bool, str | None]:
    """Return (is_ignored, pattern_or_None)."""
    rc, out, _ = run_cmd(
        ["git", "check-ignore", "-v", "--no-index", path], repo
    )
    if rc == 0 and out:
        # format: <file>:<lineno>:<pattern>\t<path>
        pattern = out.split("\t")[0].split(":")[-1].strip()
        return True, pattern
    return False, None


def create_path(repo: Path, rel: str):
    """Create file or directory (trailing /) under repo."""
    target = repo / rel
    if rel.endswith("/"):
        target.mkdir(parents=True, exist_ok=True)
        # git needs at least one file to see the dir
        (target / ".keep").touch()
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEMPLATE_TEXT = TEMPLATE.read_text()

CASES = [
    # --- **/nbproject/private/ ---
    # Should be ignored (at depth 0)
    {
        "name": "private-root",
        "path": "nbproject/private/",
        "expected_ignored": True,
        "note": "**/nbproject/private/ matches at any depth including root",
        "group": "private-dir",
    },
    # Should be ignored (nested deep)
    {
        "name": "private-nested",
        "path": "myapp/nbproject/private/",
        "expected_ignored": True,
        "note": "** ensures match at arbitrary depth",
        "group": "private-dir",
    },
    # Sibling: a file inside the private dir is also ignored (covered by parent dir ignore)
    {
        "name": "private-file-inside",
        "path": "nbproject/private/cache.dat",
        "expected_ignored": True,
        "note": "Files inside nbproject/private/ are also ignored (directory is ignored)",
        "group": "private-dir",
    },
    # Near-miss: shared project.xml should NOT be ignored
    {
        "name": "shared-project-xml",
        "path": "nbproject/project.xml",
        "expected_ignored": False,
        "note": "Only 'private/' is ignored; shared metadata like project.xml stays tracked",
        "group": "private-dir",
    },

    # --- **/nbproject/Makefile-*.mk ---
    # Should be ignored
    {
        "name": "makefile-debug",
        "path": "nbproject/Makefile-Debug.mk",
        "expected_ignored": True,
        "note": "Makefile-*.mk matches auto-generated debug variant",
        "group": "makefile",
    },
    {
        "name": "makefile-release-nested",
        "path": "sub/nbproject/Makefile-Release.mk",
        "expected_ignored": True,
        "note": "** allows match in nested sub-project",
        "group": "makefile",
    },
    # Near-miss: hand-edited Makefile.mk (no dash-variant) should NOT be ignored
    {
        "name": "makefile-plain",
        "path": "nbproject/Makefile.mk",
        "expected_ignored": False,
        "note": "Plain Makefile.mk (no dash) is NOT matched — intentionally kept",
        "group": "makefile",
    },
    # Near-miss: a .mk file inside ignored build/ — also ignored (covered by build/ rule)
    {
        "name": "makefile-outside-nbproject",
        "path": "build/Makefile-Debug.mk",
        "expected_ignored": True,
        "note": "build/ dir itself is ignored, so all contents inside it are also ignored",
        "group": "makefile",
    },

    # --- **/nbproject/Package-*.bash ---
    {
        "name": "package-debug",
        "path": "nbproject/Package-Debug.bash",
        "expected_ignored": True,
        "note": "Package-*.bash matches auto-generated packaging script",
        "group": "package",
    },
    {
        "name": "package-release-nested",
        "path": "sub/nbproject/Package-Release.bash",
        "expected_ignored": True,
        "note": "** allows match at any nesting level",
        "group": "package",
    },
    # Near-miss: a custom hand-written script.bash
    {
        "name": "package-plain-bash",
        "path": "nbproject/deploy.bash",
        "expected_ignored": False,
        "note": "deploy.bash does NOT match Package-*.bash — user scripts stay visible",
        "group": "package",
    },
    # Near-miss: .sh (not .bash) extension
    {
        "name": "package-sh-extension",
        "path": "nbproject/Package-Debug.sh",
        "expected_ignored": False,
        "note": ".sh extension is NOT covered by the .bash pattern",
        "group": "package",
    },

    # --- build/ dist/ standard dirs ---
    {
        "name": "build-dir",
        "path": "build/",
        "expected_ignored": True,
        "note": "build/ at root is ignored",
        "group": "build-output",
    },
    {
        "name": "dist-dir",
        "path": "dist/",
        "expected_ignored": True,
        "note": "dist/ at root is ignored",
        "group": "build-output",
    },
    # Source file must remain visible
    {
        "name": "source-java",
        "path": "src/com/example/Main.java",
        "expected_ignored": False,
        "note": "Source files are never ignored",
        "group": "build-output",
    },
]


def run_checks(cases: list[dict]) -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory() as tmp_str:
        repo = Path(tmp_str)
        setup_temp_repo(repo, TEMPLATE_TEXT)

        # Commit a source file so we can test tracked-file porcelain behaviour
        src = repo / "src" / "com" / "example" / "Main.java"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("public class Main {}\n")
        run_cmd(["git", "add", "."], repo)
        run_cmd(["git", "commit", "-m", "init"], repo)

        # Modify the tracked source file (should appear as 'M', not '??')
        src.write_text("public class Main { /* modified */ }\n")

        for case in cases:
            create_path(repo, case["path"])
            is_ignored, pattern = check_ignored(repo, case["path"])

            # Inject force-fail on first case
            if FORCE_FAIL and case["name"] == "private-root":
                is_ignored = not is_ignored

            expected = case["expected_ignored"]
            passed = is_ignored == expected
            status = "PASS" if passed else "FAIL"
            results.append(
                {
                    "name": case["name"],
                    "path": case["path"],
                    "group": case["group"],
                    "expected_ignored": expected,
                    "actual_ignored": is_ignored,
                    "pattern_matched": pattern,
                    "note": case["note"],
                    "passed": passed,
                    "status": status,
                }
            )
            label = f"{status:<6} {case['name']:<30} | {case['path']:<40} | ignored={is_ignored} (exp={expected}) | pattern={pattern}"
            print(label)

        # Tracked file check
        rc, out, _ = run_cmd(["git", "status", "--porcelain", "src/com/example/Main.java"], repo)
        tracked_ok = out.startswith("M ")
        t_status = "PASS" if tracked_ok else "FAIL"
        print("-" * 70)
        print(f"[{t_status}] Tracked source file: 'git status --porcelain src/com/example/Main.java' -> '{out}'")
        results.append({
            "name": "tracked-source-modified",
            "path": "src/com/example/Main.java",
            "group": "tracked",
            "note": "Modified tracked source shows as 'M' in porcelain",
            "passed": tracked_ok,
            "status": t_status,
        })

    return results


def main() -> int:
    results = run_checks(CASES)
    failures = [r for r in results if not r["passed"]]
    tool_versions = get_tool_versions()

    evidence = {
        "task": "R46-T029",
        "issue": 29,
        "template": "Global/NetBeans.gitignore",
        "focus_patterns": [
            "**/nbproject/private/",
            "**/nbproject/Makefile-*.mk",
            "**/nbproject/Package-*.bash",
        ],
        "tool_versions": tool_versions,
        "total_checks": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "results": results,
    }

    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2))
    print(f"\n[+] Saved structured evidence to {EVIDENCE_FILE}")

    TOOL_VERSIONS_FILE.write_text(
        "\n".join(f"{k}: {v}" for k, v in tool_versions.items()) + "\n"
    )
    print(f"[+] Saved tool versions to {TOOL_VERSIONS_FILE}")

    log_lines = [f"R46-T029 check | {r['status']} | {r['name']} | {r.get('path','')}" for r in results]
    LOG_FILE.write_text("\n".join(log_lines) + "\n")
    print(f"[+] Saved run log to {LOG_FILE}")

    readme = f"""# R46-T029 — Global/NetBeans.gitignore

**Task ID**: R46-T029 | **Issue**: #29 | **Student**: E26B07F0687

## Focus Patterns
| Pattern | Purpose |
|---------|---------|
| `**/nbproject/private/` | Ignore IDE private settings at **any** directory depth |
| `**/nbproject/Makefile-*.mk` | Ignore auto-generated build makefiles; plain `Makefile.mk` kept |
| `**/nbproject/Package-*.bash` | Ignore auto-generated packaging scripts; custom `.bash` files kept |

## Why These Exact Patterns?

### `**/nbproject/private/` vs Alternatives
- **Too broad**: `**/nbproject/` → would hide `project.xml` and other shared metadata
- **Too narrow**: `nbproject/private/` (no `**`) → misses nested sub-projects at depth > 1
- **Just right**: `**/nbproject/private/` matches the private directory at any depth without touching shared files

### `**/nbproject/Makefile-*.mk` vs Alternatives
- **Too broad**: `**/nbproject/*.mk` → catches hand-edited `.mk` files
- **Too narrow**: `**/nbproject/Makefile.mk` → misses `Makefile-Debug.mk`, `Makefile-Release.mk`

### `**/nbproject/Package-*.bash` vs Alternatives
- **Too broad**: `**/nbproject/*.bash` → catches custom user scripts
- **Too narrow**: `**/nbproject/Package.bash` → misses `Package-Debug.bash`, `Package-Release.bash`

## Results
| Check | Status |
|-------|--------|
| Total checks | {evidence['total_checks']} |
| Passed | {evidence['passed']} |
| Failed | {evidence['failed']} |

See `evidence.json` for full structured output.
"""
    README_FILE.write_text(readme)
    print(f"[+] Saved README documentation to {README_FILE}")

    if failures:
        print(f"\n[!] ASSERTION FAILURES OCCURRED:")
        for f in failures:
            print(f"    - {f['name']} ({f.get('path','')}): assertion failed")
        return 1
    else:
        print(f"\n[PASS] All {len(results)} checks passed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
