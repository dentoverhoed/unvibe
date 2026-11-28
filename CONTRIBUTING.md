# Contributing to unvibe

Thanks for helping. There are two useful things you can do.

## 1. Tell us how `/kickstart` went

Ran it on your repo? [Open a run report](https://github.com/dentoverhoed/unvibe/issues/new?template=run-report.yml). It takes two minutes. The most useful reports include:
- the stack;
- the command you typed;
- what the agent did, and what you expected.

One concrete repro beats ten opinions.

Before you paste output, remove secrets, customer data and internal URLs. `/kickstart` never prints secret values, but your code might.

## 2. Improve the skill

The skill is three files: `skills/kickstart/SKILL.md` routes to sections of `skills/kickstart/runbook.md`, and `/kickstart workflow` to `skills/kickstart/workflow.md`. All three are prompts, so every line costs the agent context on every run.

### What makes a good change
- **It fixes something an agent actually got wrong.** Show the run where it went wrong. "This would be nicer" is not enough.
- **It's short.** Prefer one precise sentence over a paragraph. If a rule can be checked mechanically, add a check, not prose. `check_skill.py` holds a word budget for the skill; raising it needs a reason in your PR.
- **It's phrased positively.** Write "use X", not "NEVER do Y", and leave out CAPITALS and IMPORTANT.
- **It keeps routing intact.** SKILL.md points to runbook sections by heading name. If you rename a heading, update the route. `scripts/check_skill.py` catches mismatches.
- **It's credited.** A new practice names its source, which goes in the README credits.

### Before you open a PR
1. Run `python scripts/check_skill.py`. CI runs it too.
2. Build the demo shop: `python examples/make_demo_shop.py ../demo-shop`.
3. Run the [eval scenarios](evals/README.md) your change affects, at least scenario 1. Changed the security quick scan? Also run the security recall check on a private repo ([evals/README.md](evals/README.md#security-recall-at-scale-manual-on-a-private-repo)).
4. Using Claude Code? Ask the read-only `reviewer` agent in `.claude/agents/` to review your diff in a fresh context.
5. Fill in the PR template, including the evals table. You must have read and tested your own PR before asking anyone else to.

## Decisions we already made

Proposals that reopen these are welcome, but they need new evidence.

| Decision | Why | Rejected |
|---|---|---|
| Install by **copying** (`scripts/install.py`) | The installed skill changes only when you run the script, never because a branch with half-finished edits is checked out | A symlink or junction to the repo. A Claude Code plugin is deferred, not rejected. |
| **No markdownlint** | All 353 hits were style rules (line length, blank lines). Reformatting the runbook costs context and catches nothing that breaks. | Linting with most rules disabled. `check_skill.py` checks structure instead. |
| **Evals run by hand**, not in CI | Each run costs tokens, and a person has to judge behaviour. The results go into the PR. | A `claude -p` runner on every push |
| A **word budget**, not a fixed cap | It sits just above today's size, so raising it is a visible, explained change in a PR | A hard cap with lots of slack, which never bites |
| The fixture is **generated**, not committed | A nested git repo with a committed `.env` can't live cleanly inside this repo. Fixed dates keep its hashes stable. | A git bundle or tarball, which is binary and unreviewable |
| External links are checked **weekly** | A flaky site should never block a contribution. Relative links are checked on every PR. | Lychee on every PR |
| **No auto-merge**, including Dependabot | Every change to the skill or CI gets a human decision | Auto-merging two-way doors |

## License

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE).
