# R46-T001 — Dart.gitignore fixtures

## Actual template rules tested

The test loads `Dart.gitignore` from the repository. Focus patterns:

```gitignore
.dart_tool/
.packages
build/
```

## Positive fixtures (expected: IGNORED)

| File / path | Pattern | Line | Result |
|---|---|---|---|
| `.dart_tool/config.json` | `.dart_tool/` | 5 | Ignored |
| `.packages` | `.packages` | 6 | Ignored |
| `build/output.txt` | `build/` | 7 | Ignored |
| `sub/build/output.txt` | `build/` | 7 | Ignored |

## Negative fixtures (expected: NOT ignored — near-miss names)

| File / path | Reason | Result |
|---|---|---|
| `.dart_tool-file` | Trailing-slash pattern only matches directories | Not ignored |
| `.packages-backup` | Exact name match required | Not ignored |
| `build.txt` | `build/` only matches directories | Not ignored |

## Tracked-file behaviour

A tracked `.packages` file remains visible after a `.gitignore` rule is in place:

- `git check-ignore -v .packages` returns exit 1 (not ignored).
- `git check-ignore -v --no-index .packages` returns exit 0 and identifies `.packages` at line 6.

## Tool versions

See `versions.txt`.
