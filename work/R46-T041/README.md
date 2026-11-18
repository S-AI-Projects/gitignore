# R46-T041 evidence

The check builds a disposable Git repository under this directory, writes the
selected Calabash ignore rules to its `.gitignore`, creates each fixture, and
asserts both the ignore classification and the exact rule reported by Git.
The temporary repository is removed when the check exits. Fixtures are never
created in the project checkout.

Run from the repository root:

```sh
python3 work/R46-T041/check.py
```

`results.json` records expected and actual classifications, the rule line
reported by `git check-ignore -v --no-index`, tracked-file status, and tool
versions. Exit status 1 from `git check-ignore` is treated as the expected
not-ignored result; any classification, rule, or status mismatch raises an
assertion and exits non-zero.

## Near misses

- `rerun.txt` is a file, not a directory named `rerun`.
- `reports.yml` is a file, not a directory named `reports`.
- `screenshots-old/` has a different directory name from `screenshots/`.
- `src/screenshots.py` is a source file, not a path inside a `screenshots/`
  directory.

The unanchored directory rules also match below nested paths, as demonstrated
by `app/reports/` and `app/screenshots/`.

## Source

- Template at pinned revision: `Global/Calabash.gitignore` in
  `S-AI-Projects/gitignore`, commit `6bb5af7a1b050e5add3a71b6e6365c93498822ac`.
- Contribution policy: `CONTRIBUTING.md` at that same revision. It asks for a
  focused single-template change, a reason, and supporting documentation.
- The PR change is a comment documenting the already-existing directory
  matching behavior; the three rules themselves are unchanged.
