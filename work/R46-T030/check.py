#!/usr/bin/env python3
"""
Verification check for R46-T030 (Issue #30):
Template: CFWheels.gitignore
Focus patterns:
  - plugins/**/*
  - files
  - db/sql

Goal:
Demonstrate a realistic CFWheels project tree:
  - tracked source (controllers, models, views, config)
  - untracked/ignored runtime artifacts (plugin binaries, uploaded files, SQL migrations, bundles)

Checks line-number attribution with `git check-ignore -v --no-index`
and tracked-file behaviour with `git status --porcelain`.

Outputs: work/R46-T030/evidence.json, tool_versions.txt, run.log, README.md
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
TEMPLATE = REPO_ROOT / "CFWheels.gitignore"
EVIDENCE_FILE = TASK_DIR / "evidence.json"
TOOL_VERSIONS_FILE = TASK_DIR / "tool_versions.txt"
LOG_FILE = TASK_DIR / "run.log"
README_FILE = TASK_DIR / "README.md"

FORCE_FAIL = os.environ.get("R46_T030_FORCE_FAIL", "0") == "1"


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


def setup_temp_repo(tmp: Path, gitignore_text: str) -> None:
    run_cmd(["git", "init", "-b", "main"], tmp)
    run_cmd(["git", "config", "user.email", "test@test.com"], tmp)
    run_cmd(["git", "config", "user.name", "Test"], tmp)
    gi = tmp / ".gitignore"
    gi.write_text(gitignore_text)


def check_ignored(repo: Path, path: str) -> tuple[bool, str | None, str | None]:
    """Return (is_ignored, pattern_or_None, source_line_or_None)."""
    rc, out, _ = run_cmd(["git", "check-ignore", "-v", "--no-index", path], repo)
    if rc == 0 and out:
        # format: <file>:<lineno>:<pattern>\t<path>
        parts = out.split("\t")[0].split(":")
        line_no = parts[1] if len(parts) >= 2 else None
        pattern = parts[2].strip() if len(parts) >= 3 else None
        return True, pattern, line_no
    return False, None, None


def create_path(repo: Path, rel: str) -> None:
    target = repo / rel
    if rel.endswith("/"):
        target.mkdir(parents=True, exist_ok=True)
        (target / ".keep").touch()
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()


# ---------------------------------------------------------------------------
# Realistic CFWheels project tree test cases
# ---------------------------------------------------------------------------
#
# Tracked (source):  controllers/, models/, views/, config/settings.cfm
# Ignored (runtime): plugins/**/*, files (upload dir), db/sql, bundles
# ---------------------------------------------------------------------------

CASES = [
    # --- plugins/**/* ---
    # Nested plugin file (should be ignored)
    {
        "name": "plugin-nested-file",
        "path": "plugins/DBMigrate/index.cfm",
        "expected_ignored": True,
        "note": "plugins/**/* matches files at any depth inside plugins/",
        "group": "plugins",
    },
    {
        "name": "plugin-deep-asset",
        "path": "plugins/Wheels/assets/images/logo.png",
        "expected_ignored": True,
        "note": "plugins/**/* matches deeply nested plugin assets",
        "group": "plugins",
    },
    # Near-miss: source controller should NOT be ignored
    {
        "name": "controller-not-ignored",
        "path": "controllers/Account.cfc",
        "expected_ignored": False,
        "note": "Source files in controllers/ are never ignored",
        "group": "plugins",
    },
    # plugins/ directory itself — also ignored (git extends the ** rule to cover parent dir)
    {
        "name": "plugins-root-itself",
        "path": "plugins/",
        "expected_ignored": True,
        "note": "Git also ignores the plugins/ directory itself under plugins/**/* in --no-index mode",
        "group": "plugins",
    },

    # --- files ---
    # The 'files' rule ignores a file OR directory named 'files' at any path
    {
        "name": "files-upload-dir",
        "path": "files/",
        "expected_ignored": True,
        "note": "'files' pattern matches the top-level upload directory",
        "group": "files",
    },
    {
        "name": "files-nested-upload",
        "path": "files/images/avatar.jpg",
        "expected_ignored": True,
        "note": "Contents inside ignored 'files/' are also ignored",
        "group": "files",
    },
    # Near-miss: source config file must remain visible
    {
        "name": "config-settings",
        "path": "config/settings.cfm",
        "expected_ignored": False,
        "note": "config/ source files are never ignored",
        "group": "files",
    },
    # Near-miss: a file called 'fileslist.txt' — NOT matched ('files' is exact name)
    {
        "name": "fileslist-not-matched",
        "path": "fileslist.txt",
        "expected_ignored": False,
        "note": "'files' pattern matches exact name only; 'fileslist.txt' is not ignored",
        "group": "files",
    },

    # --- db/sql ---
    {
        "name": "db-sql-migration",
        "path": "db/sql/001_create_users.sql",
        "expected_ignored": True,
        "note": "db/sql matches the directory at repo root; migration SQL inside is ignored",
        "group": "db-sql",
    },
    {
        "name": "db-sql-nested-script",
        "path": "db/sql/rollbacks/002_drop_users.sql",
        "expected_ignored": True,
        "note": "db/sql ignores the whole sub-tree rooted at db/sql",
        "group": "db-sql",
    },
    # Near-miss: hand-written seed data in db/ (not in db/sql/) should stay visible
    {
        "name": "db-seed-not-sql",
        "path": "db/seeds.cfm",
        "expected_ignored": False,
        "note": "db/seeds.cfm is outside db/sql — it stays tracked",
        "group": "db-sql",
    },
    # Near-miss: a sql file elsewhere is NOT ignored
    {
        "name": "sql-outside-db",
        "path": "deploy/schema.sql",
        "expected_ignored": False,
        "note": "db/sql only anchors to repo root; deploy/schema.sql is NOT ignored",
        "group": "db-sql",
    },

    # --- bundles (AssetBundler) ---
    {
        "name": "js-bundle",
        "path": "javascripts/bundles/app.min.js",
        "expected_ignored": True,
        "note": "javascripts/bundles/ is ignored — generated bundles are not committed",
        "group": "bundles",
    },
    {
        "name": "css-bundle",
        "path": "stylesheets/bundles/main.min.css",
        "expected_ignored": True,
        "note": "stylesheets/bundles/ is ignored",
        "group": "bundles",
    },
    # Near-miss: source JS in javascripts/ (outside bundles/) stays visible
    {
        "name": "js-source",
        "path": "javascripts/app.js",
        "expected_ignored": False,
        "note": "Source JS outside bundles/ is NOT ignored",
        "group": "bundles",
    },
]


def run_checks(cases: list[dict]) -> list[dict]:
    results = []
    template_text = TEMPLATE.read_text()
    with tempfile.TemporaryDirectory() as tmp_str:
        repo = Path(tmp_str)
        setup_temp_repo(repo, template_text)

        # Commit a source controller so we can verify tracked-file behavior
        ctrl = repo / "controllers" / "Account.cfc"
        ctrl.parent.mkdir(parents=True, exist_ok=True)
        ctrl.write_text("<cfcomponent></cfcomponent>\n")
        run_cmd(["git", "add", "."], repo)
        run_cmd(["git", "commit", "-m", "init source"], repo)

        # Modify tracked source (should show as 'M' in porcelain)
        ctrl.write_text("<cfcomponent><!-- modified --></cfcomponent>\n")

        for case in cases:
            create_path(repo, case["path"])
            is_ignored, pattern, line_no = check_ignored(repo, case["path"])

            if FORCE_FAIL and case["name"] == "plugin-nested-file":
                is_ignored = not is_ignored

            expected = case["expected_ignored"]
            passed = is_ignored == expected
            status = "PASS" if passed else "FAIL"
            results.append({
                "name": case["name"],
                "path": case["path"],
                "group": case["group"],
                "expected_ignored": expected,
                "actual_ignored": is_ignored,
                "pattern_matched": pattern,
                "gitignore_line": line_no,
                "note": case["note"],
                "passed": passed,
                "status": status,
            })
            label = (
                f"{status:<6} {case['name']:<28} | {case['path']:<42} | "
                f"ignored={is_ignored} (exp={expected}) | pattern={pattern} (line {line_no})"
            )
            print(label)

        # Tracked file check
        rc, out, _ = run_cmd(
            ["git", "status", "--porcelain", "controllers/Account.cfc"], repo
        )
        tracked_ok = out.startswith("M ")
        t_status = "PASS" if tracked_ok else "FAIL"
        print("-" * 70)
        print(f"[{t_status}] Tracked source: 'git status --porcelain controllers/Account.cfc' -> '{out}'")
        results.append({
            "name": "tracked-controller-modified",
            "path": "controllers/Account.cfc",
            "group": "tracked",
            "note": "Modified tracked source shows as 'M' in porcelain — not ignored",
            "passed": tracked_ok,
            "status": t_status,
        })

    return results


def main() -> int:
    results = run_checks(CASES)
    failures = [r for r in results if not r["passed"]]
    tool_versions = get_tool_versions()

    evidence = {
        "task": "R46-T030",
        "issue": 30,
        "template": "CFWheels.gitignore",
        "focus_patterns": ["plugins/**/*", "files", "db/sql"],
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

    LOG_FILE.write_text(
        "\n".join(f"R46-T030 | {r['status']} | {r['name']} | {r.get('path','')}" for r in results) + "\n"
    )
    print(f"[+] Saved run log to {LOG_FILE}")

    readme = f"""# R46-T030 — CFWheels.gitignore

**Task ID**: R46-T030 | **Issue**: #30 | **Student**: E26B07F0687

## Realistic Project Tree

```
myapp/
  controllers/Account.cfc        ← tracked source
  models/User.cfc                ← tracked source
  views/account/index.cfm        ← tracked source
  config/settings.cfm            ← tracked source
  plugins/DBMigrate/index.cfm   ← IGNORED (plugins/**/*) — binary plugin
  plugins/Wheels/assets/logo.png ← IGNORED (plugins/**/*) — deep plugin asset
  files/images/avatar.jpg        ← IGNORED (files) — user upload
  db/sql/001_create_users.sql    ← IGNORED (db/sql) — generated migration
  db/seeds.cfm                   ← TRACKED  — hand-written seed
  javascripts/bundles/app.min.js ← IGNORED (javascripts/bundles) — generated
  stylesheets/bundles/main.min.css ← IGNORED (stylesheets/bundles) — generated
  javascripts/app.js             ← TRACKED  — source JS
```

## Focus Patterns

| Pattern | Purpose |
|---------|---------|
| `plugins/**/*` | Ignore all files inside plugins/ at any depth; dir itself stays visible |
| `files` | Ignore the runtime upload directory (file or dir named 'files') |
| `db/sql` | Ignore auto-generated SQL migrations; hand-written db scripts tracked |

## Pattern Analysis

### `plugins/**/*` vs Alternatives
- `plugins/` → entire directory hidden, losing folder structure in git tree
- `plugins/*` → only one level deep; misses `plugins/Wheels/assets/logo.png`
- `plugins/**/*` → ignores **all file content** while keeping folder scaffolding visible ✓

### `files` vs Alternatives
- `files/` → only matches if 'files' is a directory; misses edge cases
- `files` → matches both a file and a directory named 'files' ✓

### `db/sql` vs Alternatives
- `db/` → too broad; hides hand-written `db/seeds.cfm`
- `db/sql/*.sql` → misses files without `.sql` extension
- `db/sql` → ignores the entire sub-tree under `db/sql/` ✓

## Results
| Check | Count |
|-------|-------|
| Total | {evidence['total_checks']} |
| Passed | {evidence['passed']} |
| Failed | {evidence['failed']} |

See `evidence.json` for full structured evidence.
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
