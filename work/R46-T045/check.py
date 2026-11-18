#!/usr/bin/env python3
"""Check JBoss deployment ignores and tracked-file behavior in a temporary repo."""
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


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def inspect(repo, fixture):
    result = run(["git", "check-ignore", "-v", "--no-index", "--", fixture["path"]], repo, check=False)
    expect(result.returncode in (0, 1),
           f"check-ignore returned {result.returncode} for {fixture['path']}: {result.stderr}")
    ignored = result.returncode == 0
    rule = result.stdout.rstrip("\n").split("\t", 1)[0] if ignored else ""
    fields = rule.rsplit(":", 2) if rule else []
    pattern = fields[2] if fields else None
    line = int(fields[1]) if fields else None
    expect(ignored == fixture["ignored"],
           f"{fixture['path']}: expected ignored={fixture['ignored']}, got {ignored}")
    expect(pattern == fixture["pattern"],
           f"{fixture['path']}: expected pattern={fixture['pattern']!r}, got {pattern!r}")
    expect(line == fixture["line"],
           f"{fixture['path']}: expected rule line={fixture['line']!r}, got {line!r}")
    return {
        "pattern_name": fixture["pattern_name"],
        "case": fixture["case"],
        "path": fixture["path"],
        "expected_ignored": fixture["ignored"],
        "actual_ignored": ignored,
        "expected_pattern": fixture["pattern"],
        "actual_pattern": pattern,
        "expected_rule_line": fixture["line"],
        "actual_rule_line": line,
        "git_output": result.stdout.strip(),
    }


def main():
    python = run(["python3", "--version"], ROOT)
    git = run(["git", "--version"], ROOT)
    versions = {"python": python.stdout.strip() or python.stderr.strip(),
                "git": git.stdout.strip() or git.stderr.strip()}
    records = []

    with tempfile.TemporaryDirectory(prefix="r46-t045-", dir=HERE) as temp:
        repo = pathlib.Path(temp)
        run(["git", "init", "-q"], repo)

        # Track the matching fixture in a commit before adding the ignore template.
        tracked = FIXTURE_DATA["tracked_path"]
        tracked_file = repo / tracked
        tracked_file.parent.mkdir(parents=True, exist_ok=True)
        tracked_file.write_text("tracked before ignore template\n")
        run(["git", "add", "--", tracked], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "commit fixture before ignore template"], repo)

        (repo / ".gitignore").write_text(TEMPLATE)
        run(["git", "add", "--", ".gitignore"], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "apply JBoss ignore template"], repo)

        for fixture in FIXTURE_DATA["fixtures"]:
            if fixture["path"] == tracked or not fixture["ignored"]:
                continue
            path = repo / fixture["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
            if fixture["ignored"]:
                records.append(inspect(repo, fixture))

        status_after_ignored_untracked = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        expect(status_after_ignored_untracked == "",
               f"ignored untracked fixtures should not appear in status: {status_after_ignored_untracked!r}")
        tracked_check = run(["git", "ls-files", "--error-unmatch", "--", tracked], repo)
        expect(tracked_check.returncode == 0, f"tracked fixture left the index: {tracked}")

        tracked_file.write_text("modified after ignore template\n")
        status_after_tracked_edit = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        expected_tracked_status = f" M {tracked}"
        expect(status_after_tracked_edit == expected_tracked_status,
               f"expected {expected_tracked_status!r}, got {status_after_tracked_edit!r}")
        tracked_behavior = {
            "path": tracked,
            "tracked_before_template_commit": True,
            "status_with_new_ignored_matches": status_after_ignored_untracked,
            "expected_status_with_new_ignored_matches": "",
            "status_after_tracked_edit": status_after_tracked_edit,
            "expected_status_after_tracked_edit": expected_tracked_status,
        }

        for fixture in FIXTURE_DATA["fixtures"]:
            if fixture["ignored"]:
                if fixture["path"] == tracked:
                    records.append(inspect(repo, fixture))
                continue
            path = repo / fixture["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("near miss\n")
            records.append(inspect(repo, fixture))

    output = {"tool_versions": versions, "results": records,
              "tracked_file_behavior": tracked_behavior}
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
