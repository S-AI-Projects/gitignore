
# R46-T003 — Ninja ignore fixtures

## Actual template rules

The test copies `Global/Ninja.gitignore` into a temporary Git repository.

```gitignore
.ninja_deps
.ninja_log
```

For the negation demonstration, the test appends this local rule:

```gitignore
!build/.ninja_log
```

## Test fixtures

| File | Expected result | Actual result |
|---|---|---|
| `.ninja_deps` | Ignored | Ignored |
| `build/.ninja_deps` | Ignored | Ignored |
| `.ninja_log` | Ignored | Ignored |
| `build/.ninja_log` | Not ignored | Not ignored |
| `.ninja_deps-backup` | Not ignored | Not ignored |
| `.ninja_log-backup` | Not ignored | Not ignored |

## Negation demonstration

Git uses the last matching rule to determine whether a file is ignored.

The original `.ninja_log` pattern matches `build/.ninja_log`.

The later `!build/.ninja_log` rule overrides that ignore rule, so `build/.ninja_log` is not ignored.

## Tracked-file behaviour

A tracked `.ninja_deps` file remains tracked.

Normal `git check-ignore` does not report tracked files as ignored.

Using `git check-ignore -v --no-index` identifies the matching ignore rule even for a tracked file.

## Test result

All automated checks passed.

## Tool versions

Git 2.55.0

Python 3.14.7
