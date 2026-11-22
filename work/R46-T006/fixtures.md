# R46-T006 — Modelica.gitignore fixtures

## Task type: Case and path portability

This task tests the selected patterns with space-containing paths and records
filesystem case behaviour explicitly.

## Actual template rules tested

The test loads `Modelica.gitignore` from the repository. Focus patterns:

```gitignore
*~
*.bak
*.bak-mo
```

## Positive fixtures (expected: IGNORED)

| File / path | Pattern | Line | Result |
|---|---|---|---|
| `model.mo~` | `*~` | 12 | Ignored |
| `my model.mo~` | `*~` | 12 | Ignored (space in name) |
| `model.bak` | `*.bak` | 13 | Ignored |
| `sub dir/component.bak` | `*.bak` | 13 | Ignored (space in path) |
| `model.bak-mo` | `*.bak-mo` | 14 | Ignored |
| `subpackage/component.bak-mo` | `*.bak-mo` | 14 | Ignored |

## Negative fixtures (expected: NOT ignored)

| File / path | Reason | Result |
|---|---|---|
| `model.mo` | Modelica source; no matching rule | Not ignored |
| `package.order` | Package metadata; no matching rule | Not ignored |
| `modelbak` | No `.bak` extension | Not ignored |
| `modelbak-mo` | No `.bak-mo` extension | Not ignored |

## Case behaviour

- `core.ignorecase = true` (macOS default; APFS is case-insensitive).
- `model.bak` (canonical case) is ignored by `*.bak`.
- `MODEL.BAK` is also ignored on this filesystem (`core.ignorecase=true`).
- On Linux (`core.ignorecase=false`), `MODEL.BAK` would NOT be matched.

## Space-containing paths

Both `"my model.mo~"` and `"sub dir/component.bak"` are correctly ignored.
Git gitignore patterns do not require shell quoting; spaces are literal.

## Tool versions

See `versions.txt`.
