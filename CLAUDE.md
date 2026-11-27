# unvibe

The product is a prompt: `skills/kickstart/SKILL.md` routes to sections of `skills/kickstart/runbook.md`. Every line there costs context on every run, so prefer one precise sentence, or a check, over a paragraph.

## Commands
- Checks: `python scripts/check_skill.py`. It covers frontmatter, routed headings, block names, relative links and a word budget for the skill. CI also builds the fixture on Ubuntu, Windows and macOS.
- Fixture: `python examples/make_demo_shop.py <folder outside this repo>`. It prints `HEAD: b7fc963 | self-test: 1 passed`.
- Install: `python scripts/install.py`, or `--check` to see what's out of date. Tests: `python scripts/test_install.py`, which needs a clean `skills/kickstart/`.
- Evals: the scenarios and MUST / MUST NOT tables are in `evals/README.md`.
- Stop hook: `.claude/settings.json` runs the checks before you end a turn. If they fail, fix them first.
- Review: use the read-only `reviewer` agent in `.claude/agents/` on a skill diff, in a fresh context.

## Rules you can't see in the code
- SKILL.md points to runbook sections by heading name. Renaming a heading means updating the route in SKILL.md too.
- A block name (S, F, V, H, T, R, Re, A, Au) is identical in the Phase 2 table, the Phase 3 heading and the README table.
- Fixture content is pinned. Any change to the files or commits in `make_demo_shop.py` changes all three commit hashes (`b43e17d`, `a5ab331`, `b7fc963`). Find every place they appear with `git grep -nE "b43e17d|a5ab331|b7fc963"`, and use the new hashes the script prints. A change can also shift the line numbers that `docs/example-report.md` cites.
- `docs/example-report.md` and the README demo block are real agent output. Re-wrap them, but leave the findings as they are.
- Repo text is English. The skill itself replies in the user's language.
- A new practice in the runbook gets its source in the README credits table.

## Misleading spots
- The README demo mentions `docs/agents/audit-2026-11-27.md`. That file belongs to the demo shop, not to this repo.
- `docs/agents/` here is gitignored: it holds local `/kickstart` reports about unvibe itself.
- The commit hashes in `docs/example-report.md` (`c3be5fc`, …) differ from the fixture's (`b43e17d`, …). This is on purpose, as `evals/README.md` explains.
