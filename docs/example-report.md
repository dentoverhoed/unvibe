# Audit demo-shop — 2026-11-27 @ 4a60203

## Summary (max 10 lines)
- Tiny Python "webshop": a dict-routed `handle(req)` (`shop/api.py`) over an in-memory `DB` dict (`shop/orders.py`). 3 files of code, 1 test.
- Tests run (`python -m pytest`: 1 passed, 0.03 s), but nothing covers the discount rule, refunds or the API.
- **Security-urgent:** `.env` is committed (since `c3be5fc`) and not in `.gitignore`; `/debug` dumps the whole DB; `/chargeback` has no authorization.
- No dependency manifest, no lint/typecheck, no CI, no git remote, no agent config (CLAUDE.md, `.claude/`).
- The discount rule is duplicated (`orders.py:7-8` and `orders.py:21-22`); the only fix in history (`d6e1e3c`) changed it in both places and was reverted (`4a60203`) — untested business rule.
- Domain synonyms: refund / chargeback / reversed for one concept.

## Scorecard
| Dimension | Score | Evidence |
|---|---|---|
| Tests | 1 | 1 test (`tests/test_orders.py:2`), passes, single-file run works; no coverage of discount, refund, api |
| Types and lint | 0 | no ruff/mypy/flake8 config or tool installed; no type hints |
| Agent verification | 1 | `handle()` can be driven via `python -c` (verified); no CLI/server, no seed, no logs |
| Harness | 0 | no CLAUDE.md / AGENTS.md / `.claude/settings.json`; no deny rule for `.env` |
| Shared language | 0 | refund (`orders.py:12`) = chargeback (`api.py:5`) = status "reversed" (`orders.py:14`); no glossary |
| Architecture | 1 | tiny, but duplicated discount logic and a global mutable `DB` imported by the API layer |
| Review and PR | 0 | no PR template, no review setup |
| Security baseline | 0 | `.env` tracked + not ignored; `/debug` open; no authz; no input validation |
| CI/CD and branch protection | 0 | no CI config; no git remote (`git remote -v` empty) |

## Commands (test / single test file / typecheck / lint / build / start)
- Test: `python -m pytest` (from `README.md:2`) — 1 passed in 0.03 s (Python 3.14.3, pytest 9.0.3)
- Single test file: `python -m pytest tests/test_orders.py -q` — 1 passed in 0.01 s
- Typecheck: not found
- Lint: not found
- Build: not applicable (no manifest; not found)
- Start: not found. Drive in-process: `python -c "from shop.api import handle; print(handle({'path':'/order','user':'a','items':[{'price':60,'qty':2}]}))"` → `{'id': 1}` (verified)

## Codebase map
- Modules and responsibilities
  - `shop/api.py` — request router: `handle(req)` dispatches on `req["path"]` (`/order`, `/chargeback`, `/debug`); returns `None` for unknown paths (verified).
  - `shop/orders.py` — in-memory store `DB` (`:1`), order creation with discount (`:3-10`), refund (`:12-15`), `invoice_total` (`:17-23`, no callers found in repo).
  - `shop/__init__.py` — empty.
  - `tests/test_orders.py` — one test for `create_order` under the discount threshold.
- Core flows (call-stack trees with file:line)
  - Place order
    ```
    handle(req) shop/api.py:2
    └─ path == "/order" shop/api.py:3
       └─ create_order(user, items) shop/orders.py:3
          ├─ sum price*qty shop/orders.py:5-6
          ├─ total > 100 → total*0.9 shop/orders.py:7-8
          └─ DB[len(DB)+1] = {..., status "new"} shop/orders.py:9 → returns id :10
    ```
  - Chargeback / refund
    ```
    handle(req) shop/api.py:2
    └─ path == "/chargeback" shop/api.py:5
       └─ refund(int(req["id"])) shop/orders.py:12
          └─ DB[order_id]["status"] = "reversed" shop/orders.py:13-14 (KeyError if id unknown)
    ```
  - Debug dump
    ```
    handle(req) shop/api.py:2
    └─ path == "/debug" shop/api.py:7 → returns whole DB shop/api.py:8-9
    ```

## Domain terms (seed for GLOSSARY.md) + synonyms found
- order (`create_order`, `/order`), item (price, qty), total, invoice total (`invoice_total`), discount (implicit: 10 % above 100), status (`new`, `reversed`), user.
- **Synonyms:** refund (`orders.py:12`) / chargeback (`api.py:5`) / reversed (`orders.py:14`) — one action, three names. In payments these normally mean different things (unverified which is meant).

## Misleading spots
- `invoice_total` (`orders.py:17`) looks like the canonical price calculation but has no callers; `create_order` recomputes the total itself. Changing one without the other diverges them.
- Order IDs are `len(DB)+1` (`orders.py:9`): safe only while nothing is ever deleted.
- Money is computed as float (`total * 0.9`) — `108.0` observed.

## Hotspots and recurring mistake types
- History: 3 commits, all 2026-11-27. `shop/orders.py` changed in all 3.
- `d6e1e3c fix discount` changed 0.9 → 0.85 in both duplicates; `4a60203` reverted it. Mistake type: business rule changed without a test, in duplicated code. No test covers totals above 100.

## Guardrails: present / missing
- Present: `.gitignore` (`__pycache__/`, `.pytest_cache/` only); a runnable test.
- Missing: dependency manifest (pyproject/requirements), CI, pre-commit, lint rules, type checking, module-boundary rules, branch protection (no remote), CLAUDE.md/AGENTS.md, `.claude/settings.json` (hooks, deny rules), `.env` in `.gitignore`.

## Security quick scan
- **Secrets:** `.env` is tracked (`git ls-files .env`), not ignored (`git check-ignore` negative), and in history since `c3be5fc`. Contents not opened. Treat any secret in it as leaked.
- **Debug endpoint:** `/debug` returns all orders incl. user and items (`api.py:7-9`), no auth.
- **Authorization:** `/chargeback` reverses any order for any caller (`api.py:5-6`); no ownership check.
- **Input validation:** none. `int(req["id"])` raises on non-numeric; unknown id → KeyError (`orders.py:13`); negative price/qty accepted (`orders.py:6`).
- **Dependency advisories:** no manifest, so nothing to audit; `pip-audit` not installed.

## Architecture signals
- Duplicated code: discount + sum in `create_order` and `invoice_total` (`orders.py:4-8` ↔ `:18-22`).
- Global mutable state `DB` imported directly by the API (`api.py:8`) — no storage interface.
- No god files or import cycles (codebase is 32 lines).
- The single test asserts on internal `DB` rather than a returned value (`test_orders.py:4`).

## Action list
| ID | Block | What | Why (evidence) | Size | Door | Blast radius | Depends on |
|---|---|---|---|---|---|---|---|
| S1 | Security | Rotate any secrets in `.env`; `git rm --cached .env`; add `.env` to `.gitignore`; add `.env.example`. History rewrite = separate decision | `.env` tracked since `c3be5fc`, not ignored | S | rotate/untrack: two-way; history rewrite: one-way | all environments using those secrets | — |
| S2 | Security | Remove or guard `/debug` | `api.py:7-9` dumps whole DB | S | two-way | API callers of `/debug` | — |
| S3 | Security | Authorization + validation on `/chargeback` (only owner/admin; validate id) | `api.py:5-6`, `orders.py:13` | M | two-way | refund flow | F1 (tests first) |
| F1 | Foundation | `pyproject.toml` with pytest dev-dep; tests for discount threshold (≤100, >100), refund, api routes | no manifest; discount untested (`d6e1e3c`/`4a60203`) | S | two-way | tests only | — |
| F2 | Foundation | Add ruff + mypy (config + commands) | no lint/typecheck | S | two-way | dev tooling | F1 |
| F3 | Foundation | CI running test + lint + typecheck | no CI, no remote | S | two-way | repo | F1, F2, git host (open question) |
| V1 | Verification | CLI driver `python -m shop.cli '<json>'` with seed data, JSON output as evidence | only `python -c` driving possible | S | two-way | new file only | F1 |
| H1 | Harness | Lean CLAUDE.md (commands, glossary pointer) + `.claude/settings.json` deny `Read(.env*)` | no agent config | S | two-way | agent sessions | S1 |
| T1 | Language | `GLOSSARY.md`: decide refund vs chargeback vs reversed | synonyms `api.py:5`, `orders.py:12,14` | S | two-way | docs (rename later) | — |
| R1 | Ratchet | Test: `create_order` total == `invoice_total` for same items | duplicated rule diverged in `d6e1e3c` | S | two-way | tests only | F1 |
| Re1 | Review | PR template (Appendix E) + read-only reviewer step | none present | S | two-way | process | F3 |
| A1 | Architecture | Single `order_total()` used by both paths; storage behind an interface | `orders.py:4-8` ↔ `:18-22`; `api.py:8` | M | two-way | orders module | F1, R1 |

Autonomy (Au) not proposed: human decision only.

## Open questions
1. Does `.env` contain real credentials that must be rotated? Is a git-history rewrite wanted (one-way door)?
2. Is the discount 10 % or 15 % above 100? Why was `d6e1e3c` reverted?
3. Refund, chargeback and "reversed": one concept or different ones?
4. Who may trigger a chargeback? Is there a user/auth model somewhere?
5. Which git host will this live on (needed for CI and branch protection)? Is there a real HTTP server outside this repo?
