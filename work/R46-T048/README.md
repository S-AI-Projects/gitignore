# R46-T048 KDevelop 4 ignore regression

Run from the repository root:

```sh
python3 work/R46-T048/check.py
```

The checker creates an isolated temporary Git repository and copies the real
`Global/KDevelop4.gitignore` into it. It runs `git check-ignore -v --no-index`
for every fixture, asserting both classification and the matching rule/line.
For expected visible paths, exit code 1 is treated as not ignored. It also
checks `git status --porcelain` and edits a tracked source fixture to demonstrate
that ignore rules do not hide tracked files.

`fixtures.json` records the input paths and expected classification;
`results.json` records actual rule lines, observed status, and tool versions.
