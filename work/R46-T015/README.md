# Task R46-T015: Explain Already-Tracked Files in Global/Windows.gitignore

## Focus Patterns
- `Thumbs.db`
- `Thumbs.db:encryptable`
- `ehthumbs.db`

## Why Git Ignore Rules Do Not Untrack Files

A fundamental tenet of Git's architecture is that `.gitignore` patterns only apply to **untracked** files. Git uses ignore patterns to determine whether newly encountered untracked files in the working directory should be presented in `git status` as untracked candidates for staging (`git add`).

Once a file is tracked in Git's index / staging area:
1. Git tracks changes to that path regardless of `.gitignore` rules.
2. Modifying a tracked file causes `git status` to report it as modified (`M`).
3. Adding a `.gitignore` rule matching a tracked file does **not** remove it from the index.
4. To stop tracking an already-committed file, it must be explicitly removed from the index using `git rm --cached <path>`.

## Fixture Verification

### Matching Fixtures (Ignored when Untracked)
- `Thumbs.db`: Windows thumbnail cache at root (matches `Thumbs.db`).
- `assets/Thumbs.db`: Windows thumbnail cache in nested directory (matches `Thumbs.db`).
- `Thumbs.db:encryptable`: Alternate Data Stream (ADS) thumbnail cache file (matches `Thumbs.db:encryptable`).
- `ehthumbs.db`: Windows Media Center enhanced thumbnail database (matches `ehthumbs.db`).
- `media/ehthumbs.db`: Nested enhanced thumbnail database (matches `ehthumbs.db`).

### Nonmatching / Near-Miss Fixtures (Visible)
- `Thumbs.db.txt`: Text file with `.txt` extension.
- `MyThumbs.db`: Custom file with prefix `My`.
- `ehthumbs.db.bak`: Backup file.
- `Thumbs.png`: Regular user image.

### Tracked vs Untracked Comparison
In our automated test:
1. `Thumbs.db` is staged and committed to git *before* `.gitignore` is introduced.
2. `.gitignore` containing `Global/Windows.gitignore` is then applied.
3. An untracked `ehthumbs.db` is created.
4. The committed `Thumbs.db` is modified.
5. Verification:
   - `git status --porcelain` shows `M Thumbs.db`.
   - `ehthumbs.db` is suppressed completely by Git.
   - Demonstrates that `Thumbs.db` remains actively tracked until `git rm --cached` is executed.

## Automated Verification
Run the verification check:
```bash
python3 work/R46-T015/check.py
```
To verify non-zero exit on failure:
```bash
R46_T015_FORCE_FAIL=1 python3 work/R46-T015/check.py
```
