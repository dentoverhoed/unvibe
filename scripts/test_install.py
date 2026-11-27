"""Scenario tests for scripts/install.py.

    python scripts/test_install.py

Installs into a temporary project folder and checks every path: fresh install,
up to date, --check, repo changes, hand edits (refused, then --force) and
copies installed without this script. It temporarily edits skills/kickstart/
and restores it with git, so it refuses to run when that folder has
uncommitted changes. Needs the full git history (CI: fetch-depth 0).
"""
import json, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "kickstart"
results = []


def run(name, *extra, expect):
    out = subprocess.run([sys.executable, "-I", "scripts/install.py", "--project", str(PROJ), *extra],
                         cwd=REPO, capture_output=True, text=True)
    lines = [l for l in (out.stdout + out.stderr).splitlines() if not l.startswith(("skill:", "target:"))]
    ok = out.returncode == expect
    results.append(ok)
    print(f"{'OK ' if ok else 'BAD'} {name}: exit={out.returncode} (expected {expect})")
    for l in lines:
        print(f"      {l}")


def git(*a, **kw):
    return subprocess.run(["git", *a], cwd=REPO, check=True, capture_output=True, **kw).stdout


def edit(path, old, new):
    path.write_text(path.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8", newline="\n")


if git("status", "--porcelain", "--", "skills/kickstart/"):
    sys.exit("refused: skills/kickstart/ has uncommitted changes; commit or stash them first")
ROOT_COMMIT = git("rev-list", "--max-parents=0", "HEAD", text=True).split()[0]

with tempfile.TemporaryDirectory() as tmp:
    PROJ = Path(tmp)
    DEST = PROJ / ".claude" / "skills" / "kickstart"
    try:
        run("1 fresh install", expect=0)
        same = all((DEST / p.name).read_bytes() == p.read_bytes() for p in SKILL.iterdir())
        man = json.loads((DEST / ".unvibe-install.json").read_text())
        print(f"      files identical to repo: {same}; manifest commit {man['source_commit']}, files {sorted(man['files'])}")
        results.append(same)
        run("2 rerun", expect=0)
        run("5 --check when current", "--check", expect=0)

        edit(SKILL / "runbook.md", "(full procedure)", "(full procedure, v2)")
        run("3 repo changed: --check", "--check", expect=1)
        run("3 repo changed: install", expect=0)
        git("checkout", "-q", "--", "skills/kickstart/")
        run("3 back to committed version", expect=0)

        with open(DEST / "SKILL.md", "a", encoding="utf-8") as f:
            f.write("my local edit\n")
        edit(SKILL / "SKILL.md", "## Choosing", "## Choosing!")
        run("4 hand-edited install + repo differs", expect=2)
        run("4 --force", "--force", expect=0)
        git("checkout", "-q", "--", "skills/kickstart/")
        run("4 restore", expect=0)

        (DEST / ".unvibe-install.json").unlink()
        for name in ("SKILL.md", "runbook.md"):
            (DEST / name).write_bytes(git("show", f"{ROOT_COMMIT}:skills/kickstart/{name}"))
        run("6 legacy cp-install of an older committed version", expect=0)

        (DEST / ".unvibe-install.json").unlink()
        (DEST / "runbook.md").write_bytes(git("show", f"{ROOT_COMMIT}:skills/kickstart/runbook.md") + b"hand edit\n")
        run("7 legacy cp-install with a hand edit", expect=2)
    finally:
        git("checkout", "-q", "--", "skills/kickstart/")

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
