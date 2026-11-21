# Task R46-T021: Fixture Verification for MetaProgrammingSystem.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T021` (Task 1 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #21](https://github.com/S-AI-Projects/gitignore/issues/21)
- **Template**: `MetaProgrammingSystem.gitignore`

---

## 1. Focus Patterns

1. `workspace.xml` (JetBrains MPS user-specific IDE workspace configuration)
2. `junitvmwatcher*.properties` (JUnit test runner VM watcher properties and logs)
3. `build.properties` (Ant / MPS local build property overrides)

---

## 2. Pattern Analysis & Near-Miss Fixtures

### Pattern 1: `workspace.xml`
- **Purpose**: Ignores user-specific workspace state (open editor tabs, window layouts, local tool preferences).
- **Matching Fixtures (Ignored)**:
  - `workspace.xml`: Root-level MPS workspace file (`.gitignore:2:workspace.xml`).
  - `.mps/workspace.xml`: Standard JetBrains MPS project configuration folder.
  - `project/subproject/workspace.xml`: Nested workspace file in a multi-module project.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `workspace.xml.bak`: Backup file. Remains visible because gitignore pattern without wildcards requires an exact filename match.
  - `workspace.xml.dist`: Distributed sample workspace template. Must remain tracked for version control.
  - `my-workspace.xml`: Custom workspace configuration. Distinct prefix is not matched.
  - `workspace.xml~`: Editor backup with trailing tilde. Remains visible.

### Pattern 2: `junitvmwatcher*.properties`
- **Purpose**: Ignores temporary VM watcher property files generated during MPS JUnit test runs.
- **Matching Fixtures (Ignored)**:
  - `junitvmwatcher.properties`: Base watcher file with empty wildcard (`.gitignore:19:junitvmwatcher*.properties`).
  - `junitvmwatcher1234.properties`: Watcher file with process identifier.
  - `junitvmwatcher_runner_0.properties`: Watcher file with test runner label.
  - `build/test-reports/junitvmwatcher_test.properties`: Watcher file inside test directory.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `junitvmwatcher`: Missing `.properties` extension; remains visible.
  - `junitvmwatcher.props`: Truncated extension; remains visible.
  - `my_junitvmwatcher.properties`: Prefix mismatch; remains visible because the pattern requires starting with `junitvmwatcher`.
  - `junitvmwatcher.properties.sample`: Trailing extension mismatch; remains visible.

### Pattern 3: `build.properties`
- **Purpose**: Ignores local Ant / MPS build configuration overrides.
- **Matching Fixtures (Ignored)**:
  - `build.properties`: Root Ant build properties file (`.gitignore:5:build.properties`).
  - `subproject/build.properties`: Subproject build properties.
- **Non-Matching / Near-Miss Fixtures (Remain Visible)**:
  - `build.properties.sample`: Sample configuration template; must remain tracked in repository for new contributors.
  - `build.properties.template`: Template configuration file; remains visible.
  - `build_properties`: Underscore separator instead of dot; remains visible.
  - `custom-build.properties`: Custom prefixed file; remains visible.

---

## 3. Before/After Regression Analysis

In the original `MetaProgrammingSystem.gitignore`:
- `junitvmwatcher*.properties` was placed at line 2.
- `junit*.properties` was placed at line 16 under `# generated test code and test results`.
- In Git rule evaluation, later rules override earlier rules. Because `junit*.properties` matches any file beginning with `junit` and ending with `.properties`, it shadowed `junitvmwatcher*.properties`, causing Git to attribute matches to `junit*.properties`.
- **Narrow Justified Correction**: Following `CONTRIBUTING.md` ("Add new rules to the most appropriate existing section"), `junitvmwatcher*.properties` was relocated into `# generated test code and test results` after `junit*.properties`. This resolves the shadowing conflict, allows Git to report the specific `junitvmwatcher*.properties` rule, and preserves 100% of legitimate project and test files.

---

## 4. Tracked File Behavior

- Files committed before installing ignore rules (e.g., `workspace.xml` tracked input) remain tracked by Git.
- When modified, `git status --porcelain` correctly reports `M workspace.xml`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T021/check.py
```

To verify that the check fails non-zero on assertion error:
```bash
R46_T021_FORCE_FAIL=1 python3 work/R46-T021/check.py
```
