#!/usr/bin/env python3
"""Check SCons ignore path and case behavior in disposable Git repositories."""
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


def filesystem_case_probe():
    with tempfile.TemporaryDirectory(prefix="r46-t046-case-", dir=HERE) as temp:
        directory = pathlib.Path(temp)
        mixed = directory / "CaseProbeR46T046"
        lower = directory / "caseprober46t046"
        mixed.write_text("case probe\n")
        return not lower.exists()


def configure_repo(repo, filesystem_case_sensitive):
    run(["git", "init", "-q"], repo)
    initial = run(["git", "config", "--bool", "--get", "core.ignorecase"], repo, check=False)
    initial_value = initial.stdout.strip().lower() if initial.returncode == 0 else None
    expected_core_ignorecase = "false" if filesystem_case_sensitive else "true"
    run(["git", "config", "core.ignorecase", expected_core_ignorecase], repo)
    configured = run(["git", "config", "--bool", "--get", "core.ignorecase"], repo).stdout.strip().lower()
    expect(configured == expected_core_ignorecase,
           f"expected core.ignorecase={expected_core_ignorecase}, got {configured}")
    (repo / ".gitignore").write_text(TEMPLATE)
    run(["git", "add", "--", ".gitignore"], repo)
    run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
         "commit", "-qm", "add SCons template"], repo)
    return {"git_init_core_ignorecase": initial_value,
            "configured_core_ignorecase": configured}


def create_fixture(repo, fixture):
    path = repo / fixture["path"]
    if fixture["kind"] == "directory":
        path.mkdir(parents=True, exist_ok=True)
        (path / "payload.tmp").write_text("fixture\n")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n")


def inspect(repo, fixture):
    result = run(["git", "check-ignore", "-v", "--no-index", "--", fixture["query_path"]],
                 repo, check=False)
    expect(result.returncode in (0, 1),
           f"check-ignore returned {result.returncode} for {fixture['query_path']}: {result.stderr}")
    ignored = result.returncode == 0
    source_rule = result.stdout.rstrip("\n").split("\t", 1)[0] if ignored else ""
    fields = source_rule.rsplit(":", 2) if source_rule else []
    pattern = fields[2] if fields else None
    line = int(fields[1]) if fields else None
    expect(ignored == fixture["ignored"],
           f"{fixture['query_path']}: expected ignored={fixture['ignored']}, got {ignored}")
    expect(pattern == fixture["pattern"],
           f"{fixture['query_path']}: expected pattern={fixture['pattern']!r}, got {pattern!r}")
    expect(line == fixture["line"],
           f"{fixture['query_path']}: expected line={fixture['line']!r}, got {line!r}")
    return {
        "pattern_name": fixture["pattern_name"],
        "case": fixture["case"],
        "path": fixture["path"],
        "query_path": fixture["query_path"],
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
    filesystem_case_sensitive = filesystem_case_probe()
    core_configs = []
    records = []

    for number, fixture in enumerate(FIXTURE_DATA["fixtures"]):
        fixture = dict(fixture)
        if fixture["case"].startswith("case_variant"):
            # Ignore matching follows the case behavior configured in this
            # fixture repository, which is derived from the filesystem probe.
            fixture["ignored"] = not filesystem_case_sensitive
            fixture["pattern"] = {
                "sconsign": ".sconsign.dblite",
                "config_log": "config.log",
                "sconf_temp": ".sconf_temp",
            }[fixture["pattern_name"]] if fixture["ignored"] else None
            fixture["line"] = {
                "sconsign": 3,
                "config_log": 6,
                "sconf_temp": 7,
            }[fixture["pattern_name"]] if fixture["ignored"] else None
        with tempfile.TemporaryDirectory(prefix=f"r46-t046-{number}-", dir=HERE) as temp:
            repo = pathlib.Path(temp)
            core_configs.append(configure_repo(repo, filesystem_case_sensitive))
            create_fixture(repo, fixture)
            records.append(inspect(repo, fixture))
            if fixture["ignored"]:
                status = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
                expect(status == "", f"new ignored fixture should not appear in status: {status!r}")

    tracked = FIXTURE_DATA["tracked_path"]
    with tempfile.TemporaryDirectory(prefix="r46-t046-tracked-", dir=HERE) as temp:
        repo = pathlib.Path(temp)
        tracked_path = repo / tracked
        run(["git", "init", "-q"], repo)
        initial = run(["git", "config", "--bool", "--get", "core.ignorecase"], repo, check=False)
        initial_value = initial.stdout.strip().lower() if initial.returncode == 0 else None
        core_ignorecase = "false" if filesystem_case_sensitive else "true"
        run(["git", "config", "core.ignorecase", core_ignorecase], repo)
        tracked_path.write_text("tracked before ignore rules\n")
        run(["git", "add", "--", tracked], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "track fixture before template"], repo)
        (repo / ".gitignore").write_text(TEMPLATE)
        run(["git", "add", "--", ".gitignore"], repo)
        run(["git", "-c", "user.name=R46 check", "-c", "user.email=r46@example.invalid",
             "commit", "-qm", "apply SCons template"], repo)
        ignored_path = repo / FIXTURE_DATA["ignored_untracked_path"]
        ignored_path.parent.mkdir(parents=True, exist_ok=True)
        ignored_path.write_text("new ignored fixture\n")
        status_with_ignored_untracked = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        expect(status_with_ignored_untracked == "",
               f"ignored untracked file appeared in status: {status_with_ignored_untracked!r}")
        tracked_path.write_text("modified after ignore rules\n")
        status_after_tracked_edit = run(["git", "status", "--porcelain"], repo).stdout.rstrip("\n")
        expected_status = f" M {tracked}"
        expect(status_after_tracked_edit == expected_status,
               f"expected tracked status {expected_status!r}, got {status_after_tracked_edit!r}")
        tracked_behavior = {
            "path": tracked,
            "git_init_core_ignorecase": initial_value,
            "configured_core_ignorecase": core_ignorecase,
            "status_with_new_ignored_untracked": status_with_ignored_untracked,
            "expected_status_with_new_ignored_untracked": "",
            "status_after_tracked_edit": status_after_tracked_edit,
            "expected_status_after_tracked_edit": expected_status,
        }

    output = {
        "tool_versions": versions,
        "filesystem_case_sensitive": filesystem_case_sensitive,
        "core_ignorecase_by_fixture_repo": core_configs[0]["configured_core_ignorecase"],
        "git_init_core_ignorecase_by_fixture_repo": core_configs[0]["git_init_core_ignorecase"],
        "results": records,
        "tracked_file_behavior": tracked_behavior,
    }
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
