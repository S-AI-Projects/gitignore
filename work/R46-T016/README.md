# Task R46-T016: Path and Case Assumptions in Typo3.gitignore

## Focus Patterns
- `/fileadmin/user_upload/`
- `/fileadmin/_temp_/`
- `/fileadmin/_processed_/`

## Path and Case Sensitivity Analysis

### 1. Space-Containing Paths
- Git patterns match paths containing spaces without requiring quotation or escaping when matching wildcards and subdirectories.
- A path such as `fileadmin/user_upload/my company photo 2026.jpg` is properly matched and ignored by `/fileadmin/user_upload/`.
- However, if the folder itself contains spaces instead of underscores (e.g. `fileadmin/user upload/`), the literal underscore pattern does not match, keeping the path visible.

### 2. Case Sensitivity & `core.ignorecase`
- In standard POSIX environments with case-sensitive filesystems, Git path matching is strictly case-sensitive.
- When `core.ignorecase = true` (standard default on macOS APFS and Windows NTFS):
  - Case variations such as `Fileadmin/User_Upload/photo.png` are matched by `/fileadmin/user_upload/`.
- When `core.ignorecase = false`:
  - Git enforces strict byte-for-byte character case comparisons.
  - Case variant `Fileadmin/User_Upload/photo.png` is **not** matched by `/fileadmin/user_upload/`.
  - Only the exact lowercase `fileadmin/user_upload/` matches.

### 3. Anchoring and Trailing Slashes
- The leading slash `/` anchors matching to the root directory where `.gitignore` is situated; nested copies like `nested/fileadmin/user_upload/` are not matched.
- The trailing slash `/` restricts the rule to directories. A regular file named `fileadmin/user_upload` is not ignored.

## Fixture Verification

### Matching Fixtures
- `fileadmin/user_upload/image.jpg`: Standard upload (ignored).
- `fileadmin/user_upload/sample space file.png`: File with spaces inside upload directory (ignored).
- `fileadmin/_temp_/session_cache.tmp`: Temporary TYPO3 directory content (ignored).
- `fileadmin/_processed_/preview_100x100.jpg`: Processed image thumbnails (ignored).

### Nonmatching Near-Miss Fixtures
- `fileadmin/user upload/image.jpg`: Space instead of underscore in folder name (visible).
- `fileadmin/temp/cache.tmp`: Missing underscores in directory name (visible).
- `nested/fileadmin/user_upload/image.jpg`: Anchored rule does not apply to nested subfolders (visible).
- `fileadmin/user_upload` (file): Non-directory is not matched due to trailing slash (visible).

## Tracked Files Behavior
Files committed before ignore patterns are applied remain tracked. Modifications are reported by `git status --porcelain`.

## Automated Verification
Run the check script:
```bash
python3 work/R46-T016/check.py
```
To verify non-zero exit on failure:
```bash
R46_T016_FORCE_FAIL=1 python3 work/R46-T016/check.py
```
