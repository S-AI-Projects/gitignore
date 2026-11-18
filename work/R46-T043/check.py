#!/usr/bin/env python3
"""Regression checks for Global/Tags.gitignore and last-match precedence."""
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


def inspect(repo, path, expected_ignored, expected_pattern, expected_line):
    result = run(["git", "check-ignore", "-v", "--no-index", "--", path], repo, check=False)
    if result.returncode not in (0, 1):
        raise AssertionError(f"check-ignore returned {result.returncode} for {path}: {result.stderr}")
    ignored = result.returncode == 0
    rule = result.stdout.rstrip("\n").split("\t", 1)[0] if ignored else ""
    fields = rule.rsplit(":", 2) if rule else []
    actual_pattern = fields[2] if fields else None
    actual_line = int(fields[1]) if fields else None
    assert ignored == expected_ignored, (path, expected_ignored, ignored)
    assert actual_pattern == expected_pattern, (path, expected_pattern, actual_pattern)
    assert actual_line == expected_line, (path, expected_line, actual_line)
    return {"path": path, "expected_ignored": expected_ignored, "actual_ignored": ignored,
            "expected_pattern": expected_pattern, "actual_pattern": actual_pattern,
            "expected_rule_line": expected_line, "actual_rule_line": actual_line,
            "git_output": result.stdout.strip()}


def main():
    python = run(["python3", "--version"], ROOT)
    git = run(["git", "--version"], ROOT)
    versions = {"python": python.stdout.strip() or python.stderr.strip(), "git": git.stdout.strip()}
    records = []
    with tempfile.TemporaryDirectory(prefix="r46-t043-", dir=HERE) as temp:
        repo = pathlib.Path(temp)
        run(["git", "init", "-q"], repo)
        run(["git", "config", "core.ignorecase", "false"], repo)
        (repo / ".gitignore").write_text(TEMPLATE)
        for fixture in FIXTURE_DATA["fixtures"]:
            path = repo / fixture["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        for fixture in FIXTURE_DATA["fixtures"]:
            records.append(inspect(repo, fixture["path"], fixture["ignored"],
                                   fixture["pattern"], fixture["line"]))

        tracked = FIXTURE_DATA["tracked_path"]
        run(["git", "add", "-f", "--", tracked], repo)
        run(["git", "add", "--", ".gitignore"], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "add tracked fixture"], repo)
        (repo / tracked).write_text("modified after ignore\n")
        status = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        assert any(line.startswith(" M ") and tracked in line for line in status.splitlines()), status
        tracked_behavior = {"path": tracked, "expected_status": " M", "actual_status": status}

    # Counterfactual local-only rule set: prove the later !TAGS/ rule changes
    # the same TAGS/visible.txt path from ignored to visible.
    regression = []
    before_rules = "TAGS\n"
    after_rules = "TAGS\n!TAGS/\n"
    assert after_rules.splitlines()[1] == "!TAGS/"
    for label, rules, expected_ignored, expected_pattern, expected_line in [
        ("before_negation", before_rules, True, "TAGS", 1),
        ("after_negation", after_rules, False, None, None),
    ]:
        with tempfile.TemporaryDirectory(prefix=f"r46-t043-{label}-", dir=HERE) as temp:
            repo = pathlib.Path(temp)
            run(["git", "init", "-q"], repo)
            run(["git", "config", "core.ignorecase", "false"], repo)
            (repo / ".gitignore").write_text(rules)
            run(["git", "add", ".gitignore"], repo)
            run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
                 "commit", "-qm", "set local test rules"], repo)
            visible = repo / "TAGS" / "visible.txt"
            visible.parent.mkdir(parents=True)
            visible.write_text("keep this local file\n")
            item = inspect(repo, "TAGS/visible.txt", expected_ignored, expected_pattern, expected_line)
            item["case"] = label
            if label == "after_negation":
                nonmatch = repo / "TAGZ" / "visible.txt"
                nonmatch.parent.mkdir(parents=True)
                nonmatch.write_text("near miss\n")
                item["active_negation"] = {"pattern": "!TAGS/", "line": 2}
                item["visible_status"] = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
                assert "TAGS/" in item["visible_status"], item["visible_status"]
                assert inspect(repo, "TAGZ/visible.txt", False, None, None)["actual_ignored"] is False
            regression.append(item)

    output = {"tool_versions": versions, "results": records,
              "tracked_file_behavior": tracked_behavior,
              "local_negation_regression": regression}
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
