"""Structural checks for the kickstart skill. Exit 1 on any problem.

    python scripts/check_skill.py

1. SKILL.md frontmatter: name matches the folder, description <= 1024 chars
   and starts with "Use when".
2. Every runbook section SKILL.md routes to exists ("Phase 1A", "Appendix D", ...).
3. Block names agree: Phase 2 table = Phase 3 heading = README table, and
   every block letter has its own Phase 3 section.
4. Relative links in tracked Markdown files point to files that exist.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "kickstart"
errors = []


def read(path):
    return path.read_text(encoding="utf-8")


skill, runbook, readme = (read(SKILL_DIR / "SKILL.md"), read(SKILL_DIR / "runbook.md"),
                          read(ROOT / "README.md"))

# 1. Frontmatter
fm = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not fm:
    errors.append("SKILL.md: no YAML frontmatter")
else:
    fields = dict(re.findall(r"^(\w+):\s*(.*)$", fm.group(1), re.M))
    if fields.get("name") != SKILL_DIR.name:
        errors.append(f"SKILL.md: name '{fields.get('name')}' != folder '{SKILL_DIR.name}'")
    desc = fields.get("description", "")
    if not desc.startswith("Use when"):
        errors.append("SKILL.md: description must start with 'Use when'")
    if len(desc) > 1024:
        errors.append(f"SKILL.md: description is {len(desc)} chars (max 1024)")

# 2. Routed sections exist
headings = re.findall(r"^#{2,3} (.+)$", runbook, re.M)
for name in sorted(set(re.findall(r'"((?:Phase \w+|Ground rules)[^"]*)"', skill))):
    if not any(h.startswith(name) for h in headings):
        errors.append(f"SKILL.md routes to \"{name}\", but runbook.md has no such heading")
for letters in re.findall(r"Appendi(?:x|ces) ([A-Z](?:, [A-Z])*)", skill):
    for letter in letters.split(", "):
        if not any(h.startswith(f"Appendix {letter} ") for h in headings):
            errors.append(f"SKILL.md routes to Appendix {letter}, but runbook.md has none")

# 3. Block names
phase2 = runbook.split("## Phase 2", 1)[1].split("## Phase 3", 1)[0]
phase3 = runbook.split("## Phase 3", 1)[1].split("## Phase 4", 1)[0]
table = dict(re.findall(r"^\| (\w+) \| \*\*([^*]+)\*\*", phase2, re.M))
heads = {k: v.split(" (")[0].strip() for k, v in re.findall(r"^### (\w+) — (.+)$", phase3, re.M)}
readme_rows = dict(re.findall(r"^\| \*\*(\w+)\*\* \| ([^|]+?) \|", readme, re.M))
for letter, name in table.items():
    if letter not in heads:
        errors.append(f"block {letter}: no '### {letter} — ' section in Phase 3")
    elif heads[letter] != name:
        errors.append(f"block {letter}: Phase 2 '{name}' != Phase 3 '{heads[letter]}'")
    if readme_rows.get(letter) != name:
        errors.append(f"block {letter}: Phase 2 '{name}' != README '{readme_rows.get(letter)}'")

# 4. Relative links in tracked Markdown
tracked = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split()
for rel in tracked:
    text = re.sub(r"```.*?```", "", read(ROOT / rel), flags=re.S)  # skip code blocks
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"[a-z]+:|#", target):
            continue
        if not (ROOT / rel).parent.joinpath(target.split("#")[0]).exists():
            errors.append(f"{rel}: broken link -> {target}")

print(f"checked: frontmatter, {len(headings)} headings, blocks {', '.join(table)}, "
      f"links in {len(tracked)} files")
if errors:
    print("FAIL")
    print("\n".join(f"  - {e}" for e in errors))
    sys.exit(1)
print("PASS")
