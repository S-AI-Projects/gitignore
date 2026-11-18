#!/usr/bin/env python3
"""Compare SSDT-sqlproj rules with broader and narrower temporary alternatives."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_DIR.parents[1]
TEMPLATE = REPO_ROOT / "SSDT-sqlproj.gitignore"
INPUTS = json.loads((TASK_DIR / "fixtures.json").read_text(encoding="utf-8"))
FIXTURES = INPUTS["fixtures"]

ALTERNATIVES = {
    "broader": {"bin/": "bin", "obj/": "obj", "*.dacpac": "*dacpac*"},
    "narrower": {"bin/": "/bin/", "obj/": "/obj/", "*.dacpac": "/publish/*.dacpac"},
}


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    if check and result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed ({result.returncode}): {result.stderr}")
    return result


def template_for(mode: str) -> str:
    content = TEMPLATE.read_text(encoding="utf-8")
    if mode == "baseline":
        return content
    replacements = ALTERNATIVES[mode]
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line in replacements:
            lines[index] = replacements[line]
    for original in replacements:
        assert original not in lines, f"Expected to replace {original!r} in {mode} template"
    return "\n".join(lines) + "\n"


def create_file(repo: Path, relative: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"fixture: {relative}\n", encoding="utf-8")


def main() -> None:
    assert TEMPLATE.is_file(), f"Template not found: {TEMPLATE}"
    versions = {
        "python": subprocess.check_output(["python3", "--version"], text=True).strip(),
        "git": subprocess.check_output(["git", "--version"], text=True).strip(),
    }
    actual = []
    baseline_status = []
    tracked_status = []

    for mode in ("baseline", "broader", "narrower"):
        mode_fixtures = [item for item in FIXTURES if item["mode"] == mode]
        with tempfile.TemporaryDirectory(prefix=f"ssdt-sqlproj-{mode}-") as temp:
            repo = Path(temp)
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Ignore Rule Checker")
            git(repo, "config", "user.email", "checker@example.invalid")

            if mode == "baseline":
                create_file(repo, "src/main.cpp")
                git(repo, "add", "src/main.cpp")
                git(repo, "commit", "-qm", "Track legitimate source")

            (repo / ".gitignore").write_text(template_for(mode), encoding="utf-8")
            git(repo, "add", ".gitignore")
            git(repo, "commit", "-qm", f"Apply {mode} rules")

            for fixture in mode_fixtures:
                path = fixture["path"]
                if not (repo / path).exists():
                    create_file(repo, path)
                result = git(repo, "check-ignore", "-v", "--no-index", "--", path, check=False)
                if fixture["expected"] == "ignored":
                    assert result.returncode == 0, f"{mode}:{path} expected ignored, got exit {result.returncode}"
                    header, reported_path = result.stdout.rstrip("\n").split("\t", 1)
                    rule_file, line, pattern = header.split(":", 2)
                    assert rule_file == ".gitignore", f"{mode}:{path}: rule came from {rule_file!r}"
                    assert pattern == fixture["pattern"], f"{mode}:{path}: expected {fixture['pattern']!r}, got {pattern!r}"
                    assert reported_path == path, f"{mode}:{path}: Git reported {reported_path!r}"
                    rule = {"file": rule_file, "line": int(line), "pattern": pattern}
                else:
                    assert result.returncode == 1, f"{mode}:{path} expected visible, got exit {result.returncode}"
                    assert not result.stdout, f"{mode}:{path}: unexpected rule output {result.stdout!r}"
                    rule = None
                actual.append({
                    "mode": mode, "path": path, "expected": fixture["expected"],
                    "actual": "ignored" if result.returncode == 0 else "visible",
                    "expected_pattern": fixture["pattern"], "actual_rule": rule,
                    "purpose": fixture["purpose"],
                })

            if mode == "baseline":
                status = git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
                untracked_visible = {
                    fixture["path"] for fixture in mode_fixtures
                    if fixture["expected"] == "visible" and fixture["path"] != "src/main.cpp"
                }
                ignored = {fixture["path"] for fixture in mode_fixtures if fixture["expected"] == "ignored"}
                status_paths = {line[3:] for line in status}
                assert untracked_visible <= status_paths, f"Missing visible files in status: {untracked_visible - status_paths}"
                assert not (ignored & status_paths), f"Ignored paths shown in status: {ignored & status_paths}"
                assert ".gitignore" not in status_paths and "src/main.cpp" not in status_paths
                baseline_status = status

                (repo / "src/main.cpp").write_text("int main() { return 1; }\n", encoding="utf-8")
                tracked_status = git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
                assert any(line.startswith(" M") and line.endswith("src/main.cpp") for line in tracked_status), tracked_status

    result_doc = {
        "check": "PASS",
        "template": "SSDT-sqlproj.gitignore",
        "alternatives": ALTERNATIVES,
        "tool_versions": versions,
        "results": actual,
        "baseline_status_porcelain": baseline_status,
        "tracked_source_after_edit": tracked_status,
        "conclusion": "Keep the three existing patterns. Broader alternatives produce false positives; narrower alternatives miss nested build directories or DACPACs outside publish/.",
    }
    (TASK_DIR / "results.json").write_text(json.dumps(result_doc, indent=2) + "\n", encoding="utf-8")
    (TASK_DIR / "run.log").write_text(
        "Command: python3 work/R46-T049/check.py\n"
        f"Python: {versions['python']}\nGit: {versions['git']}\n"
        f"Result: PASS ({len(actual)} mode/path assertions)\n",
        encoding="utf-8",
    )
    print(json.dumps(result_doc, indent=2))


if __name__ == "__main__":
    main()
