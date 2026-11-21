# Task R46-T028: Regression Checker for GWT.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T028` (Task 8 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #28](https://github.com/S-AI-Projects/gitignore/issues/28)
- **Template**: `GWT.gitignore`

---

## 1. Goal & Focus Patterns

Template: `GWT.gitignore`. Create a reusable temporary-repository checker for this template; verify both ignored artifacts and source files that must remain visible.

Focus patterns:
1. `*.class` (Compiled Java class byte-code)
2. `*.jar` (Java archive packages and dependencies)
3. `*.war` (Web application archive deployment packages)

---

## 2. Artifact vs. Source File Verification

In Google Web Toolkit (GWT) projects, compiled byte-code and packaged distribution archives are generated artifacts that must not be committed to version control, while Java source files (`*.java`), configuration files (`web.xml`), and Maven descriptors (`pom.xml`) must remain visible.

### A. Focus Pattern: `*.class`
- **Matching Fixtures**:
  - `App.class`: Root class file (`.gitignore:2:*.class`).
  - `target/classes/com/example/MyModule.class`: Nested class file.
- **Source Files (Must Remain Visible)**:
  - `src/main/java/com/example/MyModule.java`: Legitimate Java source code.
  - `App.classifier`: Near-miss filename.

### B. Focus Pattern: `*.jar`
- **Matching Fixtures**:
  - `library.jar`: Root archive file (`.gitignore:5:*.jar`).
  - `lib/gwt-user.jar`: Nested GWT runtime library.
- **Source Files (Must Remain Visible)**:
  - `pom.xml`: Maven project build descriptor.
  - `lib/gwt-user.jar.sha1`: Checksum file.

### C. Focus Pattern: `*.war`
- **Matching Fixtures**:
  - `app.war`: Root web application package (`.gitignore:6:*.war`).
  - `target/gwt-demo.war`: Packaged target war.
- **Source Files (Must Remain Visible)**:
  - `src/main/webapp/WEB-INF/web.xml`: Web deployment descriptor.
  - `app.war.asc`: Detached signature file.

---

## 3. Tracked File Behavior

- Source configurations committed prior to applying ignore rules (e.g. `web.xml`) remain tracked.
- Modifying a pre-tracked configuration is reported as `M web.xml` by `git status --porcelain`.

---

## 4. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T028/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T028_FORCE_FAIL=1 python3 work/R46-T028/check.py
```
