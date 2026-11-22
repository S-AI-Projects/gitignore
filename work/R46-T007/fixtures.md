
# R46-T007 Test Fixtures

## Template under test: `Global/Virtuoso.gitignore`

Patterns tested: `*.log`, `panic*.log.*`, `*.cdslck*`

### Pattern mechanics

| Pattern | Description |
|---|---|
| `*.log` | Matches any file or directory ending in `.log` at any depth |
| `panic*.log.*` | Matches Virtuoso panic log files; requires a suffix after `.log.` (e.g. `panic.log.1`, `panic.log.backup`). Plain `panic.log` is **not** matched by this rule (it is matched by the broader `*.log` rule). |
| `*.cdslck*` | Matches Cadence Design System OpenAccess database lock files, including variants with suffixes (e.g. `.cdslck1`, `.cdslck.tmp`) |

---

## Suite 1 — Positive pattern checks (`*.log`, `panic*.log.*`, `*.cdslck*`)

Temporary repo `.gitignore` = exact copy of `Global/Virtuoso.gitignore`.

| # | Path | Type | Expected | Responsible rule |
|---|---|---|---|---|
| 1 | `virtuoso.log` | file | IGNORED | `.gitignore:10:*.log` |
| 2 | `simulation.log` | file | IGNORED | `.gitignore:10:*.log` |
| 3 | `rundir/lvs.log` | file nested in dir | IGNORED | `.gitignore:10:*.log` |
| 4 | `panic.log.1` | file | IGNORED | `.gitignore:11:panic*.log.*` |
| 5 | `panic_core.log.backup` | file | IGNORED | `.gitignore:11:panic*.log.*` |
| 6 | `cellLibrary.cdslck` | file | IGNORED | `.gitignore:16:*.cdslck*` |
| 7 | `layout.cdslck1` | file | IGNORED | `.gitignore:16:*.cdslck*` |

---

## Suite 2 — Negative (near-miss) pattern checks

| # | Path | Expected | Reason |
|---|---|---|---|
| 8 | `inverter.v` | NOT IGNORED | Verilog source file |
| 9 | `circuit.spi` | NOT IGNORED | SPICE netlist |
| 10 | `panic.log` | IGNORED (by `*.log`) | Plain panic log — matched by broader `*.log`, not by `panic*.log.*` |
| 11 | `logfile` | NOT IGNORED | No `.log` extension |
| 12 | `design.cds` | NOT IGNORED | Not matching `*.cdslck*` |

---

## Notes

- All tests run in temporary Git repositories; the shared project checkout is never modified.
- `panic.log` is correctly ignored by the broader `*.log` rule. The purpose of `panic*.log.*`
  is to match files like `panic.log.1` or `panic.log.backup` that have an additional extension
  segment after `.log`.
- `*.cdslck*` is a wildcard on both sides, matching `.cdslck`, `.cdslck1`, `.cdslck.tmp`, etc.
