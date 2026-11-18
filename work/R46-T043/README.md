# R46-T043 evidence

Run from the repository root:

```sh
python3 work/R46-T043/check.py
```

The check copies the complete Tags template into a disposable repository and
asserts the `TAGS` and `.TAGS` classifications, exact matching patterns, and
rule lines. Suffix near misses stay visible. It also verifies that a tracked
`.TAGS` file still appears as modified.

For precedence, a second isolated regression compares a local test `.gitignore`
containing `TAGS` with one containing `TAGS` followed by `!TAGS/`. The same
`TAGS/visible.txt` fixture is ignored before the negation and visible after it;
the output records the actual matching line before, and the active local
negation line after. `TAGZ/visible.txt` is a deliberate nonmatch. This is only
a temporary test rule set; the template change is an explanatory comment and
adds no exception rule.

`results.json` saves expected and actual classifications, Git rule output and
line numbers, tracked-file status, and tool versions. Git check-ignore exit
code 1 is treated as not ignored. Any failed assertion makes the check exit
non-zero.

Source: `Global/Tags.gitignore` and `CONTRIBUTING.md` from
`S-AI-Projects/gitignore` at commit
`6bb5af7a1b050e5add3a71b6e6365c93498822ac`. The contribution guide requests a
focused single-template change, a rationale, and supporting documentation.
