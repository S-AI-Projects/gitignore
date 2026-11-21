# Task R46-T022: Nested Path Matching in Global/CodeKit.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T022` (Task 2 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #22](https://github.com/S-AI-Projects/gitignore/issues/22)
- **Template**: `Global/CodeKit.gitignore`

---

## 1. Goal & Focus Patterns

Template: `Global/CodeKit.gitignore`. Place equivalent filenames at the repository root and two nested directories; demonstrate which rules are anchored and which apply anywhere:

1. `config.codekit` (Unanchored - CodeKit 2 project configuration)
2. `config.codekit3` (Unanchored - CodeKit 3 project configuration)
3. `/min` (Root-Anchored - CodeKit default minified build output directory)

---

## 2. Path Anchoring Analysis

### A. Unanchored Patterns: `config.codekit` & `config.codekit3`
- **Rule Syntax**: `config.codekit` and `config.codekit3` do not have a leading slash (`/`).
- **Gitignore Behavior**: A pattern without a slash matches against the basename in **any directory** throughout the entire project hierarchy.
- **Verification Across Three Depths**:
  - **Root**: `config.codekit` $\rightarrow$ **IGNORED** (matches `.gitignore:4:config.codekit`)
  - **Level 1 Nested**: `theme/config.codekit` $\rightarrow$ **IGNORED** (matches `.gitignore:4:config.codekit`)
  - **Level 2 Nested**: `theme/assets/config.codekit` $\rightarrow$ **IGNORED** (matches `.gitignore:4:config.codekit`)
- **Near-Miss Names**:
  - `config.codekit.bak` (backup file) remains **VISIBLE** (exit code 1).
  - `config.codekit.dist` (sample distribution file) remains **VISIBLE** to allow version-controlled project templates.
  - `my_config.codekit` (prefixed custom file) remains **VISIBLE**.

### B. Root-Anchored Pattern: `/min`
- **Rule Syntax**: The pattern begins with a leading forward slash `/`.
- **Gitignore Behavior**: A leading slash anchors the match strictly to the directory where the `.gitignore` file resides (the repository root). It matches `/min/` at the root, but **does not match** `min` directories located within subdirectories.
- **Verification Across Three Depths**:
  - **Root**: `min/app.js` $\rightarrow$ **IGNORED** (matches `.gitignore:8:/min`)
  - **Level 1 Nested**: `assets/min/app.js` $\rightarrow$ **VISIBLE** (exit code 1; does not match `/min`)
  - **Level 2 Nested**: `app/static/min/bundle.css` $\rightarrow$ **VISIBLE** (exit code 1; does not match `/min`)
- **Near-Miss Names**:
  - `minute.txt`: Distinct file starting with 'min' remains **VISIBLE**.
  - `minimal/bundle.js`: Distinct folder starting with 'min' remains **VISIBLE**.
  - `min.js`: Individual minified file named 'min.js' remains **VISIBLE**.

---

## 3. Tracked File Behavior

- Files committed before installing ignore rules (e.g., pre-tracked `config.codekit`) remain tracked by Git.
- Modifying a pre-tracked file is correctly reported by `git status --porcelain` as `M config.codekit`.

---

## 4. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T022/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T022_FORCE_FAIL=1 python3 work/R46-T022/check.py
```
