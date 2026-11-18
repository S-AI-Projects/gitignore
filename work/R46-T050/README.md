# R46-T050: Leiningen template usage example

Run the reproducible checker from the repository root with:

    python3 work/R46-T050/check.py

The checker creates a disposable Git repository, commits pom.xml and source
before installing the template, then checks ignored outputs and visible
near-misses with git check-ignore -v --no-index. git status --porcelain
confirms that a tracked pom.xml remains tracked and that unignored source is
visible. fixtures.json documents the example project tree; results.json and
run.log are refreshed on each successful run.

The three selected rules are unchanged. The template comment documents their
role. The test makes the distinction explicit: pom.xml is still classified as
matching by check-ignore, but its pre-existing tracked status is retained.
