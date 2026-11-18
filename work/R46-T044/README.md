# R46-T044 evidence

Run from the repository root:

```sh
python3 work/R46-T044/check.py
```

Every fixture uses its own disposable Git repository with Angular.gitignore
copied to `.gitignore`. This allows the same basename to be a root file in one
case and a root directory in another. Each directory name is also tested one
level below the root.

The selected rules have both a leading slash and a trailing slash. The leading
slash anchors the match to the root; the trailing slash limits it to a
directory. Thus root directories named `dist`, `out-tsc`, and `tmp` are
ignored, while same-named files, nested directories, and similar names remain
visible. The check asserts each classification, exact matching rule and line,
and verifies that a tracked file under root `dist/` still appears modified.

`results.json` saves expected and actual outcomes, Git output and rule lines,
tracked-file status, and tool versions. `git check-ignore` exit code 1 is
treated as not ignored; any failed assertion exits non-zero.

Source: `Angular.gitignore` and `CONTRIBUTING.md` from
`S-AI-Projects/gitignore` at commit
`6bb5af7a1b050e5add3a71b6e6365c93498822ac`. The contribution guide requests a
focused single-template change, a rationale, and supporting documentation.
