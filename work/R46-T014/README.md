# Task R46-T014: Distinguish Directories from Files in Joomla.gitignore

## Focus Patterns
- `/.htaccess`
- `/administrator/cache/*`
- `/administrator/components/com_actionlogs/*`

## Analysis: Files vs Directories and Trailing Slash Semantics

In Git's `.gitignore` specification (`gitignore(5)`):
1. **No Trailing Slash (`/.htaccess`)**:
   - A rule without a trailing slash matches both regular files and directories that share that name at the anchored path.
   - If `/.htaccess` is a regular file: it is ignored.
   - If `/.htaccess` is created as a directory (e.g. containing `/.htaccess/custom.conf`): the directory and its contents are also ignored.
   - Leading slash `/` anchors it to the root of the repository; `nested/.htaccess` remains visible.

2. **Wildcard Contents (`/administrator/cache/*`)**:
   - The trailing `/*` matches any file or subdirectory immediately contained within `/administrator/cache/`.
   - Unlike a trailing slash `/administrator/cache/` (which ignores the directory container itself, preventing git from inspecting anything inside), the wildcard `/*` ignores the children while keeping the directory node identifiable, allowing `.gitkeep` or specific exceptions to preserve the directory structure.

3. **Component Content Isolation (`/administrator/components/com_actionlogs/*`)**:
   - Ignores all dynamic component contents within the administrator subtree.
   - Sibling or frontend paths (such as `/components/com_actionlogs/`) remain visible and unaffected.

## Separate Repository Fixture Verification
- **Repository A (Standard File Fixtures)**:
  - `/.htaccess` (regular file): **Ignored** (rule `/.htaccess`).
  - `/administrator/cache/output.cache` (regular file): **Ignored** (rule `/administrator/cache/*`).
  - `/administrator/components/com_actionlogs/test.log`: **Ignored** (rule `/administrator/components/com_actionlogs/*`).
  - `components/com_actionlogs/component.php` (frontend component): **Not Ignored**.
  - `nested/.htaccess` (subfolder): **Not Ignored**.

- **Repository B (Directory Fixtures with Same Basename)**:
  - `/.htaccess/nested.conf` (`.htaccess` as directory): **Ignored** by `/.htaccess`.
  - `/administrator/cache/subfolder/nested.tmp` (nested directory under cache): **Ignored** by `/administrator/cache/*`.
  - Regular file `/administrator/cache_file`: **Not Ignored**.

## Tracked Files Behavior
Files committed before ignore patterns are applied remain tracked. `git status --porcelain` detects and displays modifications to tracked files even if they match ignore rules.

## Automated Verification
Run the verification check:
```bash
python3 work/R46-T014/check.py
```
To verify non-zero exit on failure:
```bash
R46_T014_FORCE_FAIL=1 python3 work/R46-T014/check.py
```
