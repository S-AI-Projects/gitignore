# Task R46-T018: Reusable Regression Checker for Scala.gitignore

## Focus Patterns
- `*.class`
- `*.tasty`
- `*.log`

## Pattern Analysis: Scala Build Artifacts vs Source Files

The Scala toolchain (including scalac, sbt, and dotty) produces compilation artifacts that should never be tracked:
1. `*.class`: Java Virtual Machine bytecode compiled from Scala source units (`.scala` files).
2. `*.tasty`: Typed Abstract Syntax Trees introduced in Scala 3 for cross-version compatibility and reflection.
3. `*.log`: Execution logs and build outputs generated during compilation and testing.

### Source Files & Configurations That Must Remain Visible
Legitimate application source files, test suites, and build scripts must never be caught by these rules:
- `Main.scala`, `AppSuite.scala`: Source code units.
- `build.sbt`, `project/build.properties`: SBT build definitions.
- `logback.xml`, `application.conf`: Resource configuration files.
- Near misses: Source files with filenames containing pattern substrings (e.g. `Class.scala`, `TastyDoc.scala`, `Logger.scala`).

## Fixture Verification

### Positive Fixtures (Ignored Artifacts)
- `App.class`: Root compiled JVM class (matches `*.class`).
- `target/scala-3.3.0/classes/Main.class`: Nested compiled class (matches `*.class`).
- `App.tasty`: Root Scala 3 TASTy artifact (matches `*.tasty`).
- `target/scala-3.3.0/classes/Main.tasty`: Nested Scala 3 TASTy file (matches `*.tasty`).
- `sbt.log`: Build log output at root (matches `*.log`).
- `logs/application.log`: Application runtime log (matches `*.log`).

### Negative Fixtures (Preserved Source Files)
- `src/main/scala/Main.scala`: Source code.
- `src/test/scala/AppSuite.scala`: Test suite.
- `build.sbt`: SBT build definition.
- `project/build.properties`: SBT version config.
- `src/main/resources/logback.xml`: Log config.
- `Class.scala`: Near-miss source file containing "class".
- `TastyRecipe.scala`: Near-miss source file containing "tasty".
- `Logger.scala`: Near-miss source file containing "log".

## Tracked Files Behavior
Pre-existing tracked files remain tracked by Git. Modifications are detected and reported by `git status --porcelain`.

## Automated Verification
Run the verification check:
```bash
python3 work/R46-T018/check.py
```
To verify non-zero exit on failure:
```bash
R46_T018_FORCE_FAIL=1 python3 work/R46-T018/check.py
```
