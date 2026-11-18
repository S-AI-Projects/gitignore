# R46-T045 evidence

This check proves that the three exact deployment paths in `JBoss.gitignore`
match, while similarly named files remain visible. It commits the `all` path
before applying the ignore template, then creates the `default` and `minimal`
matching files after the template is in place. The tracked fixture remains
tracked; the new matching files are ignored.

Run from the repository root:

```sh
python3 work/R46-T045/check.py
```

The script creates and removes an isolated temporary Git repository. It uses
`git check-ignore -v --no-index` to assert each classification and the
responsible pattern and rule line. It records `git status --porcelain` before
and after modifying the previously tracked fixture. Any mismatch raises an
assertion and exits non-zero.

## Near misses

- `jboss/server/all/deploy/project.ext.bak`
- `jboss/server/default/deploy/project.ext.txt`
- `jboss/server/minimal/deploy/project.ext-copy`

The rules name the exact deployment artifact path, so these alternate names
remain visible to Git. Adding `.gitignore` later does not remove files already
in the index; the tracked fixture continues to appear in status when modified.

## Sources

- `JBoss.gitignore` at pinned revision `6bb5af7a1b050e5add3a71b6e6365c93498822ac`.
- [Git ignore documentation](https://git-scm.com/docs/gitignore), including
  the note that already tracked files are unaffected by ignore rules.
- [Contribution guidelines](https://github.com/github/gitignore/blob/6bb5af7a1b050e5add3a71b6e6365c93498822ac/CONTRIBUTING.md).
