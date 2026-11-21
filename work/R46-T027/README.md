# Task R46-T027: Pattern Origin in Global/LibreOffice.gitignore

- **Student**: sumit kavishwar
- **URN**: `E26B07F0687`
- **Task ID**: `R46-T027` (Task 7 of 10)
- **Repository**: [https://github.com/S-AI-Projects/gitignore](https://github.com/S-AI-Projects/gitignore)
- **Issue**: [Issue #27](https://github.com/S-AI-Projects/gitignore/issues/27)
- **Template**: `Global/LibreOffice.gitignore`

---

## 1. Goal & Focus Pattern

Template: `Global/LibreOffice.gitignore`. Connect the selected rule to the tool output it is intended to hide; distinguish source files from lock output.

Focus pattern:
- `.~lock.*#` (LibreOffice active document session lock file)

---

## 2. Pattern Origin & Tool Behavior

1. **Origin in LibreOffice**:
   - When an office document (such as `report.odt`, `budget.ods`, or `slides.odp`) is opened for editing, LibreOffice creates a small lock file in the same directory following the exact convention `.~lock.<filename>#`.
   - The file contains single-line CSV metadata (`user,computer,date,url`) to inform other instances that the file is in use.
   - Upon a normal application close, LibreOffice deletes this file. However, if LibreOffice terminates unexpectedly or remains open during a commit, the lock file persists on disk.

2. **Rule Precision**:
   - The pattern `.~lock.*#` requires:
     - Prefix: `.~lock.`
     - Wildcard body: `*`
     - Suffix: `#`
   - This exact shape cleanly matches all lock files while preventing false positives against actual documents (`report.odt`, `budget.ods`) and near-misses.

---

## 3. Fixture Verification

### A. Matching Lock Files (Ignored)
- `.~lock.annual_report.odt#`: Root Writer lock file (`.gitignore:3:.~lock.*#`).
- `financials/.~lock.budget_2026.ods#`: Nested Calc spreadsheet lock file.
- `presentations/q4/.~lock.strategy.odp#`: Nested Impress presentation lock file.

### B. Legitimate Source Files (Must Remain Visible)
- `annual_report.odt`: Legitimate Writer document.
- `financials/budget_2026.ods`: Legitimate Calc spreadsheet.
- `presentations/q4/strategy.odp`: Legitimate Impress presentation.

### C. Near-Miss Fixtures (Visible)
- `.~lock.document.odt`: Missing trailing `#`.
- `document.odt#`: Missing leading `.~lock.` prefix.
- `lock.odt`: Regular file named `lock.odt`.

---

## 4. Tracked File Behavior

- Source documents tracked prior to applying ignore rules (e.g. `annual_report.odt`) remain tracked.
- Modifying a pre-tracked document is reported as `M annual_report.odt` by `git status --porcelain`.

---

## 5. Execution Instructions

Run the check script from the repository root:
```bash
python3 work/R46-T027/check.py
```

To verify non-zero exit on assertion failure:
```bash
R46_T027_FORCE_FAIL=1 python3 work/R46-T027/check.py
```
