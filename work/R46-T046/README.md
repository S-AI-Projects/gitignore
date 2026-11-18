# R46-T046 evidence

This check exercises the three SCons artifact patterns at the repository root
and below a directory whose name contains spaces. It also tries suffix and
case variants, recording whether this filesystem treats case-only paths as
the same and the explicit `core.ignorecase` setting used in each temporary
repository.

Run from the repository root:

```sh
python3 work/R46-T046/check.py
```

The script uses a separate disposable Git repository for each fixture so
case-only names do not collide on case-insensitive filesystems. It asserts
both ignored/not-ignored status and the matching rule and line reported by
`git check-ignore -v --no-index`. It also records `git status --porcelain` for
a tracked fixture and an ignored untracked fixture. The check exits non-zero
on any mismatch.

## Near misses

- `.sconsign.dblite.bak`
- `config.log.backup`
- `.sconf_temp-old/`
- Uppercase variants `.SCONSIGN.DBLITE`, `CONFIG.LOG`, and `.SCONF_TEMP/`

The patterns match their exact basenames anywhere in a path, including paths
with spaces. Suffix variants have different basenames. Case-variant results
are captured with the filesystem probe and Git's explicit `core.ignorecase`
setting in `results.json`.

## Sources

- `SCons.gitignore` at pinned revision `6bb5af7a1b050e5add3a71b6e6365c93498822ac`.
- [SCons homepage](https://www.scons.org/).
- [Git ignore documentation](https://git-scm.com/docs/gitignore).
- [Contribution guidelines](https://github.com/github/gitignore/blob/6bb5af7a1b050e5add3a71b6e6365c93498822ac/CONTRIBUTING.md).
