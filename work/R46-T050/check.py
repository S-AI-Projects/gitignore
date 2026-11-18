#!/usr/bin/env python3
"""Verify a Leiningen ignore-template example in an isolated temporary repo."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "Leiningen.gitignore"
INPUTS = json.loads((TASK_DIR / "fixtures.json").read_text(encoding="utf-8"))


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    if check and result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def write_file(repo: Path, relative: str, content: str = "fixture\n") -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    assert TEMPLATE.is_file(), f"Missing template: {TEMPLATE}"
    versions = {
        "python": subprocess.check_output(["python3", "--version"], text=True).strip(),
        "git": subprocess.check_output(["git", "--version"], text=True).strip(),
    }
    actual = []
    with tempfile.TemporaryDirectory(prefix="leiningen-ignore-") as temp:
        repo = Path(temp)
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Ignore Rule Checker")
        git(repo, "config", "user.email", "checker@example.invalid")

        # Establish legitimate inputs as tracked before the template exists.
        write_file(repo, "pom.xml", "<project><modelVersion>4.0.0</modelVersion></project>\n")
        write_file(repo, "src/main.clj", "(ns demo.core)\n")
        git(repo, "add", "pom.xml", "src/main.clj")
        git(repo, "commit", "-qm", "Track project inputs before ignore rules")

        (repo / ".gitignore").write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        git(repo, "add", ".gitignore")
        git(repo, "commit", "-qm", "Install Leiningen ignore template")

        for fixture in INPUTS["fixtures"]:
            relative = fixture["path"]
            path = repo / relative
            if not path.exists():
                write_file(repo, relative)
            result = git(repo, "check-ignore", "-v", "--no-index", "--", relative, check=False)
            if fixture["expected"] == "ignored":
                assert result.returncode == 0, f"{relative}: expected ignored, got exit {result.returncode}"
                header, reported_path = result.stdout.rstrip("\n").split("\t", 1)
                rule_file, line, pattern = header.split(":", 2)
                assert rule_file == ".gitignore", f"{relative}: unexpected source {rule_file!r}"
                assert pattern == fixture["pattern"], f"{relative}: expected {fixture['pattern']!r}, got {pattern!r}"
                assert reported_path == relative, f"Git reported {reported_path!r} for {relative!r}"
                rule = {"file": rule_file, "line": int(line), "pattern": pattern}
            else:
                assert result.returncode == 1, f"{relative}: expected visible, got exit {result.returncode}"
                assert result.stdout == "", f"{relative}: unexpected matching rule: {result.stdout!r}"
                rule = None
            actual.append({
                **fixture,
                "actual": "ignored" if result.returncode == 0 else "visible",
                "actual_rule": rule,
            })

        # Modify tracked inputs; ignore rules do not remove them from the index.
        write_file(repo, "pom.xml", "<project><!-- tracked edit --></project>\n")
        write_file(repo, "src/main.clj", "(ns demo.core) ; tracked edit\n")
        status = git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
        assert any(line.startswith(" M") and line.endswith("pom.xml") for line in status), status
        assert any(line.startswith(" M") and line.endswith("src/main.clj") for line in status), status
        status_paths = {line[3:] for line in status}
        visible_untracked = {
            item["path"] for item in INPUTS["fixtures"]
            if item["expected"] == "visible" and item["path"] not in {"pom.xml", "src/main.clj"}
        }
        ignored_untracked = {
            item["path"] for item in INPUTS["fixtures"]
            if item["expected"] == "ignored" and item["path"] != "pom.xml"
        }
        assert visible_untracked <= status_paths, f"Visible files missing from status: {visible_untracked - status_paths}"
        assert not (ignored_untracked & status_paths), f"Ignored files shown by status: {ignored_untracked & status_paths}"

    results = {
        "check": "PASS",
        "template": "Leiningen.gitignore",
        "tool_versions": versions,
        "tree": INPUTS["tree"],
        "results": actual,
        "tracked_input_status_after_edit": status,
        "conclusion": "The rules match the documented metadata/artifact fixtures. Tracked pom.xml and source edits remain visible in status.",
    }
    (TASK_DIR / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (TASK_DIR / "run.log").write_text(
        f"Command: python3 work/R46-T050/check.py\nPython: {versions['python']}\nGit: {versions['git']}\nResult: PASS ({len(actual)} fixture assertions)\n",
        encoding="utf-8",
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
