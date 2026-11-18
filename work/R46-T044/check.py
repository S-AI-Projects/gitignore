#!/usr/bin/env python3
"""Verify root anchoring and trailing-slash behavior in Angular.gitignore."""
import json
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE_DATA = json.loads((HERE / "fixtures.json").read_text())
TEMPLATE = (HERE / "template.gitignore").read_text()


def run(args, cwd, *, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise AssertionError(f"{args!r} failed ({result.returncode}): {result.stderr}")
    return result


def create_repo(path):
    run(["git", "init", "-q"], path)
    (path / ".gitignore").write_text(TEMPLATE)


def inspect(repo, fixture, check_path=None):
    path = check_path or fixture["path"]
    result = run(["git", "check-ignore", "-v", "--no-index", "--", path], repo, check=False)
    if result.returncode not in (0, 1):
        raise AssertionError(f"check-ignore returned {result.returncode} for {path}: {result.stderr}")
    ignored = result.returncode == 0
    rule = result.stdout.rstrip("\n").split("\t", 1)[0] if ignored else ""
    fields = rule.rsplit(":", 2) if rule else []
    actual_pattern = fields[2] if fields else None
    actual_line = int(fields[1]) if fields else None
    assert ignored == fixture["ignored"], (path, fixture["ignored"], ignored)
    assert actual_pattern == fixture["pattern"], (path, fixture["pattern"], actual_pattern)
    assert actual_line == fixture["line"], (path, fixture["line"], actual_line)
    return {"pattern_name": fixture["pattern_name"], "case": fixture["case"], "path": path,
            "expected_ignored": fixture["ignored"], "actual_ignored": ignored,
            "expected_pattern": fixture["pattern"], "actual_pattern": actual_pattern,
            "expected_rule_line": fixture["line"], "actual_rule_line": actual_line,
            "git_output": result.stdout.strip()}


def main():
    python = run(["python3", "--version"], ROOT)
    git = run(["git", "--version"], ROOT)
    versions = {"python": python.stdout.strip() or python.stderr.strip(), "git": git.stdout.strip()}
    results = []

    # Each case uses a separate repo so a same-named file and directory never collide.
    for number, fixture in enumerate(FIXTURE_DATA["fixtures"]):
        with tempfile.TemporaryDirectory(prefix=f"r46-t044-{number}-", dir=HERE) as temp:
            repo = pathlib.Path(temp)
            create_repo(repo)
            is_directory = fixture["case"] in ("root_directory", "nested_directory", "similar_directory")
            fixture_path = repo / fixture["path"]
            if is_directory:
                fixture_path.mkdir(parents=True, exist_ok=True)
                (fixture_path / "payload.txt").write_text("fixture\n")
                check_path = fixture["path"] + "/payload.txt"
            else:
                fixture_path.parent.mkdir(parents=True, exist_ok=True)
                fixture_path.write_text("fixture\n")
                check_path = fixture["path"]
            results.append(inspect(repo, fixture, check_path))

    with tempfile.TemporaryDirectory(prefix="r46-t044-tracked-", dir=HERE) as temp:
        repo = pathlib.Path(temp)
        create_repo(repo)
        tracked = FIXTURE_DATA["tracked_path"]
        tracked_file = repo / tracked
        tracked_file.parent.mkdir(parents=True, exist_ok=True)
        tracked_file.write_text("tracked before ignore\n")
        run(["git", "add", "-f", "--", tracked], repo)
        run(["git", "add", "--", ".gitignore"], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "add tracked fixture"], repo)
        tracked_file.write_text("modified after ignore\n")
        status = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        assert any(line.startswith(" M ") and tracked in line for line in status.splitlines()), status
        tracked_behavior = {"path": tracked, "expected_status": " M", "actual_status": status}

    output = {"tool_versions": versions, "results": results, "tracked_file_behavior": tracked_behavior}
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
