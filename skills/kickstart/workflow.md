# Daily workflow after the kickstart

> Loaded by `/kickstart workflow`. Apply it to this project: name its real commands, tests and modules.

## Process sized to the task
| Task | Process |
|---|---|
| Trivial (colour, typo) | Just ask |
| Small (~one session) | Short grilling → TDD → verify → PR |
| Medium | Grilling → **design note** (human reads it) → slices → PR per slice |
| Large / unfamiliar code | **Questions → task-blind research → design note → structure outline → slices** |

## For unfamiliar or large code (after Horthy)
1. **Context 1 — questions.** Read the task and write 2–8 neutral questions of the form "how does X work?", never "how would we…". Copy links and paths over verbatim.
2. **Context 2 — research.** A new context that **does not know the task** and gets only the questions. It writes a research document: commit hash in the frontmatter, headings that state the conclusion, `file:line` references, existing test patterns per section, open questions. If it's wrong, discard it and rerun with more steering.
3. **Design note** (~1 page, Appendix D in `runbook.md`). Every design question starts *open*: the agent recommends, only the human decides. Show the **existing patterns that will be followed**, so the human can say "not that pattern".
4. **Structure outline:** signatures, new types, a file-tree diff and phases, each **vertical and verifiable on its own**.
5. Implement one phase at a time: the checks run, the human checks, commit at the end of each phase. If reality differs from the plan, stop and report: "Expected / Found / Why it matters / How to proceed?"
6. **The newest document wins:** plan > outline > design > research > ticket.

## Implementing
- **TDD:** agree on the seams first; see the test **red**, then green. No tautological tests; mock only at system boundaries.
- **Vertical slices:** the first slice touches schema, logic and a minimal visible UI or endpoint. Reject a first slice of "build the service first".
- **Separate commits** for structural (refactor) and behavioural (feature/fix) changes.
- **Commit only when** all tests pass and lint/typecheck are clean.
- **Warning signs (Kent Beck):** stop and steer on loops, functionality nobody asked for, or tests being disabled or deleted.
- **After two failed corrections:** new session, with the original prompt plus "not approach X".
- **The agent also tests by hand** (app, curl, browser); every bug found that way first gets a red test.

## Context
- **One task per session**; clear between tasks (`/clear`) for focus and cost, not because of a fixed token limit.
- **Handoff to a next session:** write a short handoff or `progress.md` with goal, approach, what's done, the current problem, and pointers to documents (not copies).
- **Effort:** *medium* by default. Higher for debugging unfamiliar code, flaky tests, schema changes, security and **verifying your own work**.

## After the work: capture lessons (compound)
- **When:** only when the work corrected a wrong belief, or the same correction was needed a **second time**; work that went as planned produces none.
- **Push the lesson as high as possible:** one way to do it, then a check, then verification, then a rule in `CODING_STANDARDS.md`; only if none fits, a lesson in `docs/solutions/`.
- **One lesson at a time.**
- **Archive or close specs and plans after delivery:** stale specs mislead later agents.

## Your own craft
- **Have the agent explain hard code** in a linear walkthrough, quoting the code via grep/sed rather than retyping it, so you don't build up "cognitive debt".
- **Read the classics:** *A Philosophy of Software Design* (Ousterhout), *Domain-Driven Design* (Evans), *Working Effectively with Legacy Code* (Feathers), *Refactoring* (Fowler), *Extreme Programming Explained* (Beck).
- **Code without AI now and then.**
