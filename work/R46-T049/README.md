# R46-T049 SSDT-sqlproj regression

Run from the repository root:

```sh
python3 work/R46-T049/check.py
```

The reusable checker creates temporary Git repositories for the baseline
template and for broader/narrower alternative patterns. It uses
`git check-ignore -v --no-index`, checks each expected classification and exact
matching pattern/rule line, and validates baseline `git status --porcelain`
including a tracked source edit. The comparisons show broader false positives
and narrower false negatives. The template retains all three real rules; only
their explanatory comment is added.

`fixtures.json` holds the inputs and expected results; `results.json` records
the actual results and tool versions; `run.log` records the successful run.
