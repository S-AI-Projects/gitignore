# Task R46-T011: Fixture Verification for Global/SBT.gitignore

## Focus Patterns
- `dist/*`
- `target/`
- `lib_managed/`

## Pattern Analysis & Near-Miss Fixtures

### 1. `dist/*`
- **Pattern purpose**: Ignores all contents inside the `dist/` distribution artifacts directory located at the repository root where `.gitignore` resides.
- **Matching fixtures (ignored)**:
  - `dist/bundle.jar`: Standard distribution build artifact.
  - `dist/release.zip`: Packaged release archive in dist folder.
- **Nonmatching / Near-miss fixtures (remain visible)**:
  - `dist.sbt`: Shares the prefix `dist` as a regular file at the repository root, but is not matched because of `/`.
  - `distribution/bundle.jar`: Sibling directory named `distribution`; git pattern matching does not treat `dist/*` as a prefix wildcard for directory names.
  - `src/dist/bundle.jar`: A nested directory containing `dist/`; because `dist/*` contains a path separator `/` (not just at the end), it is anchored at the level of the `.gitignore` file, leaving nested `dist/` subdirectories visible.

### 2. `target/`
- **Pattern purpose**: Ignores any directory named `target` anywhere in the project tree (both root `target/` and nested `project/target/`).
- **Matching fixtures (ignored)**:
  - `target/scala-2.13/classes/Main.class`: Standard root compilation output directory.
  - `project/target/config-classes/Foo.class`: Nested build target directory for SBT project meta-build.
- **Nonmatching / Near-miss fixtures (remain visible)**:
  - `docs/target`: A regular file named `target`. Because of the trailing slash in `target/`, git ignores only directory trees, leaving regular files named `target` visible.
  - `target.sbt`: SBT build settings file starting with `target`.
  - `src/main/scala/Target.scala`: Legitimate Scala source file whose basename contains `Target`.

### 3. `lib_managed/`
- **Pattern purpose**: Ignores directories named `lib_managed` containing managed dependencies downloaded by SBT.
- **Matching fixtures (ignored)**:
  - `lib_managed/jars/org.scala-lang/scala-library.jar`: Managed dependency jar in root `lib_managed/`.
  - `subproject/lib_managed/bundles/plugin.jar`: Managed dependency directory inside a subproject.
- **Nonmatching / Near-miss fixtures (remain visible)**:
  - `docs/lib_managed`: A regular file named `lib_managed`; the trailing slash prevents matching non-directories.
  - `lib/unmanaged.jar`: SBT's `lib/` directory for unmanaged library dependencies, intentionally preserved for version control.
  - `lib_managed_backup.zip`: Backup zip file starting with `lib_managed`.

## Tracked Files Behavior
- A file already tracked in Git (e.g. `target/pre_existing_tracked_file.txt`) remains tracked and monitored by Git even if an ignore rule matches its path. `git status --porcelain` correctly reports modifications.

## Automated Check
Run the check script:
```bash
python3 work/R46-T011/check.py
```
To verify non-zero exit on failure:
```bash
R46_T011_FORCE_FAIL=1 python3 work/R46-T011/check.py
```
