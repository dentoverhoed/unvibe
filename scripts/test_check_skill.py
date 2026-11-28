"""Regression tests for scripts/check_skill.py: every rule must still bite.

    python scripts/test_check_skill.py

Copies the tracked files into a temporary git repo, plants one violation at a
time, and requires check_skill.py to FAIL with the expected message. It also
requires a PASS on the clean copy and on a harmless change, so a rule can't
start firing on everything either. The real working tree is never touched.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL, RUNBOOK, README = "skills/kickstart/SKILL.md", "skills/kickstart/runbook.md", "README.md"
WORKFLOW = "skills/kickstart/workflow.md"


def replace(old, new, count=1):
    def apply(root, rel):
        p = root / rel
        text = p.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError(f"test setup: {old!r} not found in {rel}")
        p.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")
    return apply


def one_word_over_budget(root, rel):
    """Grow the file to exactly budget + 1 words, whatever the budget is now."""
    import ast
    import re
    budgets = re.search(r"WORD_BUDGET = (\{.*?\})", (root / "scripts/check_skill.py").read_text(encoding="utf-8"))
    budget = ast.literal_eval(budgets.group(1))[Path(rel).name]
    p = root / rel
    text = p.read_text(encoding="utf-8")
    p.write_text(text + "\n" + " ".join(["word"] * (budget + 1 - len(text.split()))) + "\n",
                 encoding="utf-8", newline="\n")


def append(extra):
    def apply(root, rel):
        p = root / rel
        p.write_text(p.read_text(encoding="utf-8") + extra, encoding="utf-8", newline="\n")
    return apply


# (name, file, mutation, expected substring in output, or None for PASS)
CASES = [
    ("clean copy", None, None, None),
    ("description wording", SKILL, replace("description: Use when", "description: Triggers when"),
     "description must start with 'Use when'"),
    ("name != folder", SKILL, replace("name: kickstart", "name: kick-start"), "!= folder 'kickstart'"),
    ("description too long", SKILL, replace("description: Use when", "description: Use when " + "x" * 1100),
     "(max 1024)"),
    ("no frontmatter", SKILL, replace("---\nname:", "name:"), "no YAML frontmatter"),
    ("routed heading renamed", RUNBOOK, replace("## Phase 1B —", "## Phase 1-new —"),
     'routes to "Phase 1B"'),
    ("routed file missing", SKILL, replace("all of `workflow.md`", "all of `workflows.md`"),
     "SKILL.md names workflows.md, but"),
    ("routed appendix renamed", RUNBOOK, replace("## Appendix D —", "## Annex D —"), "Appendix D, but"),
    ("block without Phase 3 section", RUNBOOK, replace("### S — Security-urgent", "### Security-urgent"),
     "block S: no '### S — ' section"),
    ("Phase 3 name differs", RUNBOOK, replace("### H — Harness", "### H — Agent harness"),
     "Phase 2 'Harness' != Phase 3 'Agent harness'"),
    ("README name differs", README, replace("| **H** | Harness |", "| **H** | Harnesses |"),
     "!= README 'Harnesses'"),
    ("broken relative link", README, replace("(docs/example-report.md)", "(docs/example-reprot.md)"),
     "broken link -> docs/example-reprot.md"),
    ("link inside code block is ignored", README, append("\n```\n[x](does-not-exist.md)\n```\n"), None),
    ("runbook one word over budget", RUNBOOK, one_word_over_budget, "over its budget"),
    ("SKILL.md one word over budget", SKILL, one_word_over_budget, "over its budget"),
    ("workflow.md one word over budget", WORKFLOW, one_word_over_budget, "over its budget"),
    ("a STOP dropped from Phase 2", RUNBOOK, replace("⛔ **STOP.** Show a summary", "Show a summary"),
     "'STOP sign (U+26D4) **STOP' appears 3 times, needs 4"),
    ("the real-stop rule weakened in SKILL.md", SKILL,
     replace("Every ⛔ STOP is a real stop.", "A ⛔ STOP is a good moment to check in."),
     "'Every STOP sign (U+26D4) STOP is a real stop'"),
    ("docs/agents-only dropped from read-only", RUNBOOK,
     replace("   - The only files you write are the report files under `docs/agents/`.\n", ""),
     "'The only files you write are the report files under `docs/agents/`'"),
    ("history rewrite allowed in the same PR", RUNBOOK,
     replace("propose it as a separate decision, never in the same PR", "you may do it in the same PR"),
     "never in the same PR' appears 0 times"),
    ("secrets rule softened in the runbook", RUNBOOK, replace("never open `.env` or key files, and ", ""),
     "lost a must-keep rule: 'never open `.env`'"),
    ("secrets rule softened in SKILL.md", SKILL, replace("never open `.env` or key files, and never print values",
                                                         "keep values private"),
     "SKILL.md lost a must-keep rule: 'never open `.env`'"),
    ("config-as-diff dropped", RUNBOOK, replace("Propose configuration, never apply it silently.", "Configure as needed."),
     "'Propose configuration, never apply it silently'"),
    ("validation dropped from the security scan", RUNBOOK, replace("input validation at the edges, ", ""),
     "'input validation at the edges'"),
    ("a ground rule removed", RUNBOOK, replace("10. **Skills and plugins are optional:**", "**Skills and plugins are optional:**"),
     "has 10 numbered rules, needs 11"),
]


def make_copy(dest):
    files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True,
                           check=True).stdout.splitlines()
    for rel in files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, target)
    for args in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)


def main():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        pristine = Path(tmp) / "pristine"
        make_copy(pristine)
        for i, (name, rel, mutate, expected) in enumerate(CASES):
            # A fresh folder per case: git marks its objects read-only on
            # Windows, and TemporaryDirectory cleans those up at the end.
            work = Path(tmp) / f"case{i}"
            shutil.copytree(pristine, work)
            if mutate:
                mutate(work, rel)
            out = subprocess.run([sys.executable, "-I", "scripts/check_skill.py"], cwd=work,
                                 capture_output=True, text=True)
            text = out.stdout + out.stderr
            if expected is None:
                ok = out.returncode == 0
                want = "PASS"
            else:
                ok = out.returncode == 1 and expected in text
                want = f"FAIL with {expected!r}"
            failures += not ok
            print(f"{'OK ' if ok else 'BAD'} {name}: exit={out.returncode}, expected {want}")
            if not ok:
                print("    " + "\n    ".join(text.strip().splitlines()))
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
