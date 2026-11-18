# R46-T004 Test Fixtures

## Template under test: `Lilypond.gitignore`

```
*.pdf    ← line 1
*.ps     ← line 2
*.midi   ← line 3
*.mid    ← line 4
*.log    ← line 5
*~       ← line 6
```

All rules are bare globs (no slashes). A bare glob without a slash matches the
filename component at every directory depth and matches both files and
directories.

---

## Note on macOS case-insensitive filesystem

macOS (HFS+/APFS default) cannot hold a file and a directory with the same
name in the same directory. All fixtures therefore use different basenames for
the file and directory cases (e.g. `score.pdf` for the file, `docs.pdf` for
the directory).

---

## Suite 1 — Bare pattern checks (*.pdf, *.ps, *.midi)

Temporary repo `.gitignore` = exact copy of `Lilypond.gitignore`.

| # | Path | Type | Expected | Responsible rule |
|---|---|---|---|---|
| 1 | `score.pdf` | file | IGNORED | `.gitignore:1:*.pdf` |
| 2 | `docs.pdf` | dir | IGNORED | `.gitignore:1:*.pdf` |
| 3 | `docs.pdf/notes.ly` | file inside ignored dir | IGNORED | `.gitignore:1:*.pdf` |
| 4 | `build/output.pdf` | nested dir | IGNORED | `.gitignore:1:*.pdf` |
| 5 | `build/output.pdf/source.ly` | file inside nested ignored dir | IGNORED | `.gitignore:1:*.pdf` |
| 6 | `score.pdf.bak` | file | NOT IGNORED | — |
| 7 | `score.pdff` | file | NOT IGNORED | — |
| 8 | `render.ps` | file | IGNORED | `.gitignore:2:*.ps` |
| 9 | `engraving.ps` | dir | IGNORED | `.gitignore:2:*.ps` |
| 10 | `engraving.ps/tune.ly` | file inside ignored dir | IGNORED | `.gitignore:2:*.ps` |
| 11 | `render.ps.orig` | file | NOT IGNORED | — |
| 12 | `song.midi` | file | IGNORED | `.gitignore:3:*.midi` |
| 13 | `orchestral.midi` | dir | IGNORED | `.gitignore:3:*.midi` |
| 14 | `orchestral.midi/part.ly` | file inside ignored dir | IGNORED | `.gitignore:3:*.midi` |
| 15 | `score.ly` | file | NOT IGNORED | — |
| 16 | `README.md` | file | NOT IGNORED | — |

---

## Suite 2 — Trailing-slash comparison

Two separate temporary repos, one with `*.pdf` and one with `*.pdf/`.

| Rule | Path | Expected |
|---|---|---|
| `*.pdf` | `score.pdf` (file) | IGNORED — bare glob matches files too |
| `*.pdf` | `docs.pdf` (dir) | IGNORED |
| `*.pdf/` | `score.pdf` (file) | **NOT IGNORED** — trailing slash restricts to dirs |
| `*.pdf/` | `docs.pdf` (dir) | IGNORED |
| `*.pdf/` | `docs.pdf/notes.ly` | IGNORED (inside ignored dir) |

**Conclusion:** The original `*.pdf` rule is intentionally broad — it ignores
both generated PDF files and any directory that happens to carry a `.pdf`
extension. Switching to `*.pdf/` would stop ignoring the PDF files themselves,
which is wrong for a Lilypond project where `.pdf` is the primary build
artefact. **No change to the template is warranted.**

---

## Suite 3 — Tracked-file behaviour

`score.pdf` force-added (`git add -f`) and committed.

| Check | Expected |
|---|---|
| `git ls-files score.pdf` | File appears in index |
| `git check-ignore -v score.pdf` (index-aware) | Exit 1 — NOT reported as ignored |
| `git check-ignore -v --no-index score.pdf` | Exit 0 — pattern `.gitignore:1:*.pdf` reported |

Tracked files are shielded from gitignore rules by Git's index. A developer
who accidentally commits a `.pdf` artefact must run `git rm --cached` to remove
it from tracking; the `.gitignore` rule alone will not evict it.
