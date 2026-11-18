# R46-T042 evidence

Run from the repository root:

```sh
python3 work/R46-T042/check.py
```

The check creates a disposable Git repository under this evidence directory,
copies the Processing rules into its `.gitignore`, and exercises each selected
name at the root, one directory down, and two directories down. It treats
`git check-ignore` exit code 1 as not ignored. Assertions check classification,
the exact matching pattern, and the rule line. `results.json` records actual
Git output, expected versus actual values, tracked-file status, and tool
versions. Any mismatch raises an assertion and exits non-zero.

All three selected patterns have no leading slash or interior slash, so their
matches apply at any depth. Near misses `.DS_Store.backup`, `applet-old`, and
`application.linux-arm64-debug` remain visible because they are distinct
path-component names. The check also confirms an already tracked nested file
remains reported as modified after the ignore rule is applied.

Source: `Processing.gitignore` and `CONTRIBUTING.md` from
`S-AI-Projects/gitignore` at commit
`6bb5af7a1b050e5add3a71b6e6365c93498822ac`. The contribution guide asks for a
focused single-template change, a rationale, and supporting documentation.
The only template change is a comment clarifying the existing unanchored
matching behavior; no ignore rule changes.
