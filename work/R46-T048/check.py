#!/usr/bin/env python3
"""Regression-check Global/KDevelop4.gitignore using a disposable Git repository."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "Global" / "KDevelop4.gitignore"
FIXTURES = json.loads((TASK_DIR / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
RESULTS_PATH = TASK_DIR / "results.json"
RUN_LOG_PATH = TASK_DIR / "run.log"


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    if check and result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed ({result.returncode}): {result.stderr}")
    return result


def write_fixture(repo: Path, relative: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"fixture for {relative}\n", encoding="utf-8")


def main() -> None:
    assert TEMPLATE.is_file(), f"Template missing: {TEMPLATE}"
    tool_versions = {
        "python": subprocess.check_output(["python3", "--version"], text=True).strip(),
        "git": subprocess.check_output(["git", "--version"], text=True).strip(),
    }
    observed = []
    with tempfile.TemporaryDirectory(prefix="kdevelop4-ignore-") as temp:
        repo = Path(temp)
        run_git(repo, "init", "-q")
        run_git(repo, "config", "user.name", "Ignore Rule Checker")
        run_git(repo, "config", "user.email", "checker@example.invalid")

        source = repo / "src" / "main.cpp"
        source.parent.mkdir(parents=True)
        source.write_text("int main() { return 0; }\n", encoding="utf-8")
        run_git(repo, "add", "src/main.cpp")
        run_git(repo, "commit", "-qm", "Track legitimate source fixture")

        (repo / ".gitignore").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        run_git(repo, "add", ".gitignore")
        run_git(repo, "commit", "-qm", "Apply KDevelop4 template")

        for fixture in FIXTURES:
            relative = fixture["path"]
            if not (repo / relative).exists():
                write_fixture(repo, relative)
            matched = run_git(repo, "check-ignore", "-v", "--no-index", "--", relative, check=False)
            if fixture["expected"] == "ignored":
                assert matched.returncode == 0, f"{relative} expected ignored; got exit {matched.returncode}"
                rule_header, reported_path = matched.stdout.rstrip("\n").split("\t", 1)
                fields = rule_header.split(":", 2)
                assert len(fields) == 3, f"Unexpected check-ignore rule: {matched.stdout!r}"
                rule_file, line, pattern = fields
                assert rule_file == ".gitignore", f"{relative}: wrong source file {rule_file!r}"
                assert pattern == fixture["pattern"], f"{relative}: expected {fixture['pattern']!r}, got {pattern!r}"
                assert reported_path == relative, f"{relative}: Git reported {reported_path!r}"
                observed_rule = {"file": rule_file, "line": int(line), "pattern": pattern}
            else:
                assert matched.returncode == 1, f"{relative} expected visible; check-ignore exit was {matched.returncode}"
                assert not matched.stdout, f"{relative}: unexpected matching rule {matched.stdout!r}"
                observed_rule = None
            observed.append({
                "path": relative, "expected": fixture["expected"],
                "actual": "ignored" if matched.returncode == 0 else "visible",
                "expected_pattern": fixture["pattern"], "actual_rule": observed_rule,
            })

        status = run_git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
        visible = {item["path"] for item in FIXTURES if item["expected"] == "visible" and not item.get("source")}
        ignored = {item["path"] for item in FIXTURES if item["expected"] == "ignored"}
        status_paths = {line[3:] for line in status}
        assert visible <= status_paths, f"Visible fixtures missing from status: {sorted(visible - status_paths)}"
        assert not (ignored & status_paths), f"Ignored fixtures shown in status: {sorted(ignored & status_paths)}"
        assert ".gitignore" not in status_paths and "src/main.cpp" not in status_paths

        source.write_text("int main() { return 1; }\n", encoding="utf-8")
        tracked_status = run_git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
        assert any(line.endswith("src/main.cpp") and line.startswith(" M") for line in tracked_status), tracked_status

        result = {
            "check": "PASS", "template": "Global/KDevelop4.gitignore",
            "tool_versions": tool_versions, "fixtures": observed,
            "status_with_untracked_fixtures": status,
            "tracked_source_after_edit": tracked_status,
            "assertions": [
                "Every ignored fixture matched its expected .gitignore rule and actual Git rule line.",
                "Every visible fixture had git check-ignore exit 1 and no rule output.",
                "git status --porcelain included visible untracked fixtures and excluded ignored artifacts.",
                "An edited tracked source file remained visible in git status.",
            ],
        }
    RESULTS_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    RUN_LOG_PATH.write_text(
        "Command: python3 work/R46-T048/check.py\n"
        f"Python: {tool_versions['python']}\nGit: {tool_versions['git']}\n"
        f"Result: PASS ({len(observed)} fixtures)\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
