# R46-T005 — ModelSim.gitignore fixtures

## Task type: Tracked-file behaviour

This task demonstrates that applying a `.gitignore` rule does not untrack files
that were already committed to the Git index.

## Actual template rules tested

The test loads `ModelSim.gitignore` from the repository. Focus patterns:

```gitignore
[_@]*
*.mti
*.dat
```

## Positive fixtures (expected: IGNORED)

| File / path | Pattern | Result |
|---|---|---|
| `_transcript` | `[_@]*` | Ignored |
| `@log` | `[_@]*` | Ignored |
| `sim.mti` | `*.mti` | Ignored |
| `results.dat` | `*.dat` | Ignored |
| `subdir/wave.dat` | `*.dat` | Ignored |

## Negative fixtures (expected: NOT ignored)

| File / path | Reason | Result |
|---|---|---|
| `design.vhd` | VHDL source file; no matching rule | Not ignored |
| `testbench.sv` | SystemVerilog source; no matching rule | Not ignored |
| `README.txt` | Documentation; no matching rule | Not ignored |
| `simulationmti` | No `.mti` extension; literal string | Not ignored |
| `results.datx` | Extension is `.datx`, not `.dat` | Not ignored |

## Tracked-file behaviour demonstration

1. `_tracked_work_file` committed to Git index **before** `.gitignore` is applied.
2. `.gitignore` with `[_@]*` rule applied and committed.
3. `git ls-files _tracked_work_file` → still listed (file remains tracked).
4. `git check-ignore -v _tracked_work_file` → exit 1 (tracked file not hidden).
5. `git check-ignore -v --no-index _tracked_work_file` → identifies `[_@]*` rule.
6. A new untracked `_new_untracked` file IS ignored by `[_@]*`.

**Conclusion:** `.gitignore` rules affect untracked files only. Already-tracked
files must be explicitly removed with `git rm --cached` to stop being tracked.

## Tool versions

See `versions.txt`.
