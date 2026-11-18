# R46-T047 evidence: PuTTY PPK files

Run from the repository root:

```sh
python3 work/R46-T047/check.py
```

PuTTY uses `.ppk` for its native SSH private-key format. The `*.ppk` rule is
kept unchanged; the added template comment records that provenance. The check
creates disposable repositories and exercises a generated private-key fixture,
a nested PPK path, an example-name near miss, source, session configuration,
and a public key. It asserts the ignore result and exact `.gitignore` rule line
from `git check-ignore -v --no-index`, then uses `git status --porcelain` to
confirm the new key stays hidden while a tracked source edit remains visible.
`results.json` records expected and actual results, Git/Python versions, and
the status output. Temporary fixture repositories are removed automatically.

## Documentation

- [PuTTY PPK file format (Appendix C)](https://www.puttyssh.org/0.81/htmldoc/AppendixC.html)
- [PuTTY credentials panel documentation](https://www.puttyssh.org/0.81/htmldoc/Chapter4.html#config-ssh-auth-cred)
- [Pinned contribution guidelines](https://github.com/github/gitignore/blob/6bb5af7a1b050e5add3a71b6e6365c93498822ac/CONTRIBUTING.md)
