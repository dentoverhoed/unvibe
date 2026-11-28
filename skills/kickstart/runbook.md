# Kickstart runbook (full procedure)

> Loaded by the `/kickstart` skill; SKILL.md routes each argument to sections here. Sources and credits: README.

---

## Ground rules for the agent (always apply)

1. **Work in phases and stop at every ⛔ STOP.** Continue only when the user explicitly says "continue" or makes a choice.
2. **Phases 1 and 2 are read-only.**
   - Change no code or config. Install, commit and push nothing.
   - The only files you write are the report files under `docs/agents/`.
   - Running tests, builds and local start-up is fine. Leave the ignored caches they create, and delete nothing.
3. **Derive commands from the repo**: package.json, pyproject, Makefile, CI config, README. Never assume tools that aren't there.
4. **Propose configuration, never apply it silently.** This covers hooks, permissions, CI and lint rules. Show the exact diff first and apply only after approval.
5. **Prove every new check works:** it passes on the current code, fails on a temporary violation, and passes again after the revert. A check that never fails is not a check.
6. **One action item per session and per PR.** Update the status in `docs/agents/kickstart-status.md`: checkboxes plus the date and commit hash you worked on.
7. **Facts before opinions.** First describe how something works *now*, with `file:line` references. Advice belongs in the report.
8. **Invent nothing.** Write "not found" for what you can't find, and mark what you can't verify `(unverified)`.
9. **Secrets:** never open `.env` or key files, and never print their values. Only check whether the file exists, is in `.gitignore`, and appears in git history (`git log -- <file>`). Reports mention at most a prefix.
10. **Skills and plugins are optional:** use available ones (grill, TDD, code review, security review); the runbook works without them.
11. **Language:** write reports, notes and replies in the user's language. Keep code identifiers and established English terms (seam, blast radius, deep module) as they are.

---

## Phase 0 — Detection and status (~5 min)

1. Decide: **NEW** (an empty or nearly empty repo, or only a scaffold) or **EXISTING** (anything else).
2. Create `docs/agents/kickstart-status.md` from the template in **Appendix A**.
3. Go to **Phase 1A** (existing project) or **Phase 1B** (new project).

---

## Phase 1A — Read-only audit of an EXISTING project

Work in this order; use subagents or parallel searches for broad searching.

### 1. Run the tests first
- Find and run the test command. Note the count, how many pass, the duration, and how to run **a single test file**.
- No tests? That becomes priority 1 in the report.

### 2. Quick checks
Can you build, typecheck and lint (commands and results)? How strict is the typing (strict mode, count of `any` / `ignore`)? Does CI fail on lint and type errors?

### 3. Can an agent verify its own work?
- **Start-up:** can the app start headless from an empty or seeded state? **Driving:** via curl, a CLI, or browser automation such as Playwright or the Chrome DevTools Protocol? **Evidence:** can logs, screenshots or traces be captured?
- **Note what is missing.** This is the biggest lever: without it, the human is the verifier and the bottleneck.

### 4. Map of the codebase — task-blind
- Describe how the system works **without** knowing which feature comes next: a researcher who knows the task bends the facts toward its first idea.
- Give an overview of folders and modules and what each owns.
- Trace **2–3 core flows** end to end, e.g. login, the main business action and payment, with `file:line` references and a call-stack tree.
- Collect **domain terms** as they appear in UI, code, DB and emails. Flag synonyms for the same concept, e.g. refund, reversal and chargeback. This seeds the glossary.
- Note **misleading spots**: an old pattern that appears everywhere but must not be copied, a folder that looks dead but is live, "six ways to do the same thing".

### 5. Hotspots
- Run `git log` over the last ~3 months of activity, counted back from the latest commit. Rank files by **change count × complexity**: use the repo's complexity tool if it has one, otherwise line count and deepest indentation. The top of that list are the A candidates.
- **Trends, not verdicts:** complexity or warnings per KLOC at 2–3 older commits, read without writing files (`git show <commit>:<path>` piped into the measurement), and lines per commit (p50/p90, `git log --shortstat`).
- Which commits are fixes or reverts, and which **kinds** of mistakes keep coming back?

### 6. Guardrail inventory
Present and missing:

- **In the repo:** CI and the steps it runs, pre-commit hooks, lint rules, module-boundary rules (dependency-cruiser, import-linter, ArchUnit-style tests).
- **On the git host:** branch protection on `main`.
- **Knowledge and review:** `GLOSSARY.md`, `docs/adr/`, `docs/solutions/` or similar, a PR template, `.claude/agents/`.
- **Agent config:** `.claude/settings.json` (hooks, deny rules for `.env` and secrets); `CLAUDE.md` / `AGENTS.md` (size in lines, contents, stale or contradictory instructions); `.env` in `.gitignore`.

### 7. Security quick scan
Not a full audit, but two lists are complete even in a large repo, never sampled:
- **Sinks:** grep the project's own source (not dependencies, build output, `.env` or key files) for the stack's sinks: raw HTML (`innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `|safe`), queries or filters built from request input, shell exec, file paths from request input (`sendFile`, `download`, `readFile`, `path.join`), and fetching a user-supplied URL. Per hit: `file:line` and whether input reaches it.
- **Routes → guard:** every route or action with the authentication and authorization (role or owner) it really passes, read from code, not comments. Flag unguarded routes or actions, rules that match more than intended (unanchored or wildcard patterns, a broad rule before narrow ones), and comments that promise a check the code lacks.

Also check input validation at the edges, secrets in code or git history, dependency advisories (`npm audit`, `pip-audit`, …), and debug or admin endpoints.

### 8. Architecture signals
- God files (large, many responsibilities), duplicated code, shallow modules (many small files without a clear interface), import cycles, low locality (one change needs many edits), and tests that restate the implementation instead of testing behaviour.
- **swallowed errors:** empty or broad `catch`/`except`, `except Exception: pass`, `|| true`, `@ts-ignore`, `eslint-disable`, `# type: ignore`. Report the count per KLOC with `file:line` examples; any one in an auth or payment path is a finding of its own.

### 9. Scorecard
Fill in the scorecard from **Appendix B**.

**→ Go to Phase 2.**

---

## Phase 1B — Intake for a NEW project

Interview the user ("grilling"): **one question at a time**, each with **a recommended answer** so that "yes" is enough, and nothing you can look up yourself.

Cover at least these points:

1. **What** are we building, **for whom**, and what is the smallest version that delivers value?
2. **Core domain concepts.** This starts the glossary.
3. **One-way doors:** auth, personal data, payments, data migrations, public APIs, emails to customers. Each of these later becomes an ADR.
4. **Stack.** Default: the most strictly typed option the team knows (TypeScript strict, Python with strict type checking). A type checker is the cheapest sensor.
5. **Data and hosting.** Default: managed Postgres and push-to-deploy via CI/CD. What can be deterministic is not done by an agent.
6. **How will the agent verify a feature?** E.g. browser automation, API calls or a CLI. Decide this **before** the first feature.
7. **Risk profile.** Personal software, customer software, or financial/medical? It later sets how much autonomy the agent gets.

**→ Go to Phase 2.**

---

## Phase 2 — Report and choice

1. Write `docs/agents/audit-YYYY-MM-DD.md` from the template in **Appendix C**.
2. Build a **prioritised action list** in the default order below, adjusted to what you found. **Every item gets** an ID (e.g. `F1`), what and why (audit evidence), a size (S/M/L), its door (one-way / two-way), blast radius, and the IDs it depends on (e.g. CI depends on a dependency manifest).

| Order | Block | Why first |
|---|---|---|
| S | **Security-urgent**: rotate leaked secrets, open debug or admin endpoints, missing authorization | First. A history rewrite is a separate, one-way decision. |
| F | **Foundation**: tests run, single-file test, typecheck, lint, CI | Without this loop every later step is guesswork |
| V | **Verification**: the agent can start the app, drive it and show evidence | Stops the human from being the bottleneck |
| H | **Harness**: lean CLAUDE.md, hooks, deny rules, protected files | Enforce at harness level, not through prompts |
| T | **Language and knowledge**: GLOSSARY.md, ADRs, knowledge store, coding standards | Fewer misunderstandings, better navigation |
| R | **Ratchet checks**: mechanical mistakes become checks that only block new violations | A mistake that happened twice does not come back |
| Re | **Review setup**: fresh read-only reviewer, security axis, PR template | Catch mistakes before merge |
| A | **Architecture**: hotspots become candidates, and you deepen one module at a time | Only worthwhile once F and V are in place |
| Au | **Autonomy**: scheduled jobs, auto-merge of two-way doors, sampling | **Always a human decision, never a default** |

3. Update `kickstart-status.md`.

⛔ **STOP.** Show a summary of at most 15 lines: the scorecard and the top 5 action items. Ask which action items may be carried out.

---

## Phase 3 — Execute: one action item per session

For each action item:
1. New branch. If this ID depends on an open ID, say so and propose that one first. Commit uncommitted `docs/agents/` files first, as a separate commit on the branch.
2. Is the shape non-trivial? Then first write a **design note of ~1 page** (Appendix D). ⛔ **STOP**: the human reads that note, not a long plan.
3. Carry it out in small steps.
4. Prove that it works.
5. Review in a fresh context: a read-only reviewer agent if the repo has one (see Re), otherwise yourself, on spec, correctness and security. Tick in the PR only the checks you actually did.
6. PR using the template in Appendix E.
7. Update the status.

### S — Security-urgent
- **Leaked secret:**
  - confirm it is tracked with `git ls-files <file>`, without opening it;
  - ask the user to rotate it at the provider. ⛔ **STOP** until they confirm. You never see or print the value;
  - stop tracking the file (`git rm --cached <file>`) and add it to `.gitignore` (`.env.*` also hides `.env.example`; add `!.env.example` if the repo has one);
  - propose, as a diff, a deny rule in `.claude/settings.json`: `"permissions": { "deny": ["Read(./.env)", "Read(./.env.*)"] }`.
  - Removing it from git history is a one-way door: propose it as a separate decision, never in the same PR.
- **Open debug or admin endpoint:** remove it or put it behind authorization. Add a test proving an unauthenticated call is refused.
- **Missing authorization:** check per action (owner or role), not only per route. Test with another user's resource: it must be refused (red → green).
- **Evidence in the PR:** the test that failed and now passes. For a leaked secret: the user's confirmation of the rotation (never the value), `git ls-files <file>` now empty, and `git check-ignore <file>` matching.

### F — Foundation
- **One command per action:** test, single test file, typecheck, lint, build. Record them in package scripts or a Makefile.
- **No tests? Start with characterisation tests:** tests that pin down the *current* behaviour of the core flows through the outermost interface (HTTP, CLI, public function). Don't test line by line.
- **CI runs** typecheck, lint and tests, and fails on errors.
- **Tighten typing with a ratchet:** turn strict mode on, record existing violations in a baseline, and let CI fail only on **new** violations.

### V — Verification (the biggest lever)
Build a **verification tool** for the agent: a script, CLI or skill with these parts.

| Part | What it does |
|---|---|
| **launch** | starts the app into a usable state, from an empty data folder or seed |
| **drive** | drives the app: Playwright/browser for UI, curl for APIs, CLI calls |
| **evidence** | stores screenshots, logs and responses in a fixed folder |
| **doctor** | read-only health check: is everything running, are the ports free? |
| **cleanup** | stops only what the tool itself started, and keeps the evidence |

Also create a **feature map**, e.g. `docs/agents/features/<feature>.md`: per feature its sub-features, how a user gets there, how to drive it, and gotchas. Start with 3–5 features.

Running the tool once end to end proves this step is done.

### H — Harness
- **Keep CLAUDE.md lean:** well under 200 lines, ideally around 60.
  - **In it:** commands, misleading spots, decisions that can't be read from the code, and rules that had to be corrected twice.
  - **Not in it:** folder structure, architecture explanations, copies of scripts; the agent looks those up itself.
  - **Pointers** to everything else are descriptive, e.g. `docs/solutions/: solved problems by category, with YAML frontmatter`. Don't write "ALWAYS READ ...".
  - Only an `AGENTS.md` exists? Put `@AGENTS.md` in CLAUDE.md, or keep a single source.
  - Personal notes go in `CLAUDE.local.md`, which is gitignored.
- **Phrase rules positively** ("use X"), not as prohibitions. Don't use CAPITALS or IMPORTANT; a rule that keeps being ignored belongs in a hook or a check.
- **Propose hooks and permissions** in the project-level `.claude/settings.json`: derive the commands from the repo, show the diff, check with `/hooks` after applying, and check the schema against the current Claude Code docs. On Windows, hooks run in Git Bash, or in PowerShell if Git Bash is missing: set `"shell": "bash"` on a hook that needs bash, and test on the team's machines.

  - **For example:** `permissions.deny`: `Read(./.env)`, `Read(./.env.*)`, `Read(./secrets/**)`; `permissions.ask`: `Bash(git push *)`; a `hooks.Stop` command hook like `npm run typecheck 1>&2 || exit 2`, so the agent can't report "done" while the check fails.
  - **Edit-time blocks:** PreToolUse hooks that exit 2 on `Edit|Write` of protected files (migrations, lockfiles, `.git/`, locked tests) or new forbidden imports, and on `Bash` for `git commit --no-verify` (permission patterns are fragile for flags). Prove each with a violating and a clean stdin payload (exit 2, then 0). Bash writes bypass them; the Stop hook and CI stay the backstop. Optional: a formatter after every edit (PostToolUse).
- **Branch protection on `main`** before any scheduled or cloud agents run.

### T — Language and knowledge
- **`GLOSSARY.md`** in the root: start with the audit's terms; per term a definition plus `_Avoid_:` with synonyms not to use; no implementation details; it grows **lazily** during normal work.
- **`docs/adr/NNNN-slug.md`:** one to three sentences, only for a decision that is hard to reverse, surprising without context, *and* the result of a real trade-off.
- **`docs/solutions/<category>/<slug>.md`** for lessons learned (format in Appendix F), only when the work **corrected a wrong belief** that someone else would otherwise repeat. Overlaps an existing lesson? Update that one.
- **`CODING_STANDARDS.md`:** judgement calls only. Anything mechanically checkable becomes a check.
- **`REVIEW.md`:** the review policy. What does each severity mean, which paths are skipped, what evidence is required?

### R — Ratchet checks
Take every mistake that happened **twice** (in the audit, in reverts or in review) and push the fix as high as possible up this ladder:

```
1. Codebase / architecture  → make the mistake impossible (one way to do it, API design)
2. Static analysis          → edit-time hook, types, lint rule, boundary rule, test, CI
3. Verification             → runtime check via the verification tool
4. Prose                    → CODING_STANDARDS.md / skill / CLAUDE.md (judgement calls only)
5. Human review             → most expensive, last resort
```

- **Error messages describe the fix**, e.g. "Use `logger.track()` from `lib/telemetry`, not `console.log`", so the agent can fix it itself.
- **Existing violations** go into a baseline, so the rule only blocks new ones.
- **Exceptions** live on the offending line itself, with a reason.
- **A typical first ratchet:** swallowed errors from the audit. Baseline today's count and block new ones; the message says to handle the error or let it crash loudly.
- **Module boundaries** are enforced with a dependency check (import-linter, dependency-cruiser): import only through a module's entry point, dependencies point one way between layers, no cycles. The full check runs in the Stop hook and CI.
- Optional: a table "rule → what enforces it" in `CODING_STANDARDS.md`. Remove a rule once its mistake has become impossible.

### Re — Review setup
- **Read-only reviewer agent**, e.g. `.claude/agents/reviewer.md` with `tools: Read, Grep, Glob`. It runs in a **fresh context**, is never the agent that wrote the code, and gets the standards **pushed** into its prompt; the implementer looks them up itself.
- **Axes:**
  1. **Spec**: was what was asked for built?
  2. **Correctness and standards**, including what agents typically get wrong: does a type or compile fix change meaning? Does every new mechanism (cache, retry, layer) answer a stated requirement? Is dead code left behind? Are the assumptions written down?
  3. **Security**: always on.
- **Fixed sentence in the review prompt:** "report gaps that affect correctness, skip style". A reviewer asked to find problems always finds something, and not every finding needs fixing.
- **PR template with evidence and merge danger** (Appendix E).
- **The author reviews first.** Never open a PR with agent code or a PR description you haven't read and tested yourself.

### A — Architecture
1. Turn the hotspots from the audit into **candidates**, each with the problem and the solution in one sentence each, the win in glossary terms, and a strength (strong / worth exploring / speculative).
2. ⛔ **STOP.** The user picks one candidate. A candidate rejected for a lasting reason gets an ADR, so it doesn't come back.
3. Make one module **deeper**: a small interface with a lot of behaviour behind it.
   - Optionally design the interface twice, from different starting points, and compare.
   - Write tests against the interface.
   - **Replace** the old shallow tests, never locked characterisation tests; don't stack new ones on top.
   - **Splitting a god file:**
     1. the design note holds the cut plan: which module owns what. Split into modules, not helpers inside the same file. The human approves it at the design-note ⛔ STOP;
     2. before any split: characterisation tests through the outer interface, proven to fail when the logic breaks, then locked so the agent can't edit them (propose the hook or CODEOWNERS as a diff);
     3. one seam per step, checks green after each, no locked test changed;
     4. evidence: the input tokens a fresh agent needs for one fixed change, before and after (the session's count, or characters ÷ 4).
4. Repeat periodically; running it daily and automatically belongs only in block Au.

### Au — Autonomy (only by human decision)
Autonomy scales with verification:
- **Personal or internal tools:** sample autonomous PRs (e.g. every 5th) and review merges after the fact.
- **Customer, financial or medical software:** spend far more on verification and security. One-way doors always get human review.

**Before any unattended run, answer five questions:** what does "done" mean, can the agent check it itself, what may it touch, what stops it, and where does the result land and who signs off?

**Only by explicit human decision, never by default:** scheduled architecture PRs, auto-merge, integration branches with many parallel agents, and bypass/YOLO modes (those only in a throwaway container).

---

## Appendix A — `docs/agents/kickstart-status.md`

```markdown
# Kickstart status
- Type: EXISTING | NEW
- Last update: YYYY-MM-DD @ <commit-hash>

## Phases
- [ ] 0 Detection
- [ ] 1 Audit / intake
- [ ] 2 Report → user's choice: <IDs>

## Action items
- [ ] F1 — <title> — branch/PR: … — evidence: …
- [ ] V1 — …

## Open questions for the user
- …
```

## Appendix B — Scorecard (one point per criterion met, 0–3)

Per point, the evidence says `met`, `not met` (verifiably absent) or `(unverified)` (couldn't check); only `met` scores. Previous audit without per-criterion evidence? Compare criteria where its evidence allows; mark other dimensions `scale changed`, not a delta.

| Dimension | Criteria | Score | Evidence |
|---|---|---|---|
| Tests | the test command runs; every test passes and one file runs on its own; each core flow from step 4 has a test through the interface its users call (HTTP for a server, CLI for a tool, exported API for a library) | | |
| Types and lint | a type checker or linter runs; the checker's strict mode is on (a linter alone: not met); CI fails on new violations | | |
| Agent verification | one command (server, CLI or script) starts the app headless from an empty or seeded state; an agent can drive it without a human; evidence lands in a fixed folder (block V) | | |
| Harness | CLAUDE.md / AGENTS.md exists and is under 200 lines; deny rules keep `.env` and key files out of reach; a hook runs the checks before the agent reports done | | |
| Shared language | a glossary covers every synonym group from step 4; at least one decision record (`docs/adr/` or a decisions table); a lessons folder with at least one entry | | |
| Architecture | no source file over 1,000 lines (generated and vendored excluded); a cycle check in the repo runs and reports none; module boundaries are enforced by a check | | |
| Review and PR | a PR template asks for evidence; a reviewer agent without Edit/Write tools; its prompt or the review policy has a security axis | | |
| Security baseline | no `.env` or key file is tracked and the step-7 secret search has no hit (rotated and untracked counts; no history rewrite needed); no route or action flagged in Routes → guard, and no sink hit reached by request input; no critical or high advisory (no dependencies: met; tool missing: unverified) | | |
| CI/CD and branch protection | CI runs on every push or PR; CI runs the tests and fails on errors; `main` requires checks and refuses direct pushes, by protection or ruleset (no remote: not met) | | |

## Appendix C — `docs/agents/audit-YYYY-MM-DD.md`

```markdown
# Audit <project> — YYYY-MM-DD @ <commit>

## Summary (max 10 lines)
## Scorecard (Appendix B criteria: met / not met / unverified per point)
## Commands (test / single test file / typecheck / lint / build / start)
## Codebase map
- Modules and responsibilities
- Core flows (call-stack trees with file:line)
## Domain terms (seed for GLOSSARY.md) + synonyms found
## Misleading spots
## Hotspots and recurring mistake types
## Guardrails: present / missing
## Security quick scan
- Sinks: hit count per pattern; every hit reached by request input (file:line)
- Routes → guard: count per guard; every flagged route
- Validation, secrets, advisories, debug/admin endpoints
## Architecture signals
## Action list
| ID | Block | What | Why (evidence) | Size | Door | Blast radius | Depends on |
## Open questions
```

## Appendix D — Design note (~1 page; the human reads this, not the long plan)

```markdown
# Design: <title>
## Current state (user's perspective, no paths)
## Desired end state
## What we are NOT doing
## Proposed approach (modules and interfaces that change)
## Design questions (open — options, pros/cons, recommendation)
## Decided (decision — reason — rejected options)
## Existing patterns to follow (existing snippet ↔ proposed)
## Verification: how do we prove it works?
```

## Appendix E — PR body

```markdown
## Summary
<smallest visual that does the job: tree, pseudocode, mermaid>
## Evidence
<before/after — screenshot, the test that failed and now passes, or real command output>
## Merge danger
- Door: two-way | one-way
- Blast radius: <one word>
## Checks
- [ ] Read and tested by the author
- [ ] Spec review  - [ ] Standards/correctness  - [ ] Security
- [ ] Glossary/ADR/solutions updated where needed
```

## Appendix F — Lesson in `docs/solutions/<category>/<slug>.md`

```markdown
---
title: <conclusion in one sentence>
problem_type: bug | best_practice | convention | architecture | tooling
module: <module>
tags: [..]
date: YYYY-MM-DD
---
## Problem / symptoms
## What didn't work
## Solution
## Why it works
## Prevention (which check/rule prevents a repeat?)
```
<!-- Reference file + function and PR numbers, not line numbers or commit SHAs (those go stale). -->
