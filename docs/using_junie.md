I have a question: Whenever specifying and developing a system, I end up working almost exclusively with AI Assistant, like I'm doing now. Documentation and code are produced. But I never see a chance to use Junie...

## Why it feels like “there’s never a chance to use Junie”

What you’re doing with AI Assistant is **interactive pair-programming**: you steer, it suggests, you iterate. That’s ideal when:

- requirements are still moving,
- you’re exploring design,
- you need lots of small decisions and judgement calls.

**Junie-style workflows** (agentic/automation) shine later, when the project has a “contract” that lets an agent operate *without asking you every minute*. If that contract is missing, using Junie feels awkward because it can’t reliably decide what “done” means.

So the “chance to use Junie” appears when you can answer three questions precisely:

1) **What should be changed?** (a bounded task)
2) **How do we know it worked?** (tests / checks)
3) **What must not change?** (constraints)

You’ve recently created that for Phase 1: install command, tests, and a smoke run.

---

## The real difference: *Assistant helps you think; Junie helps you execute*

### AI Assistant is best for
- writing/refining specs and docs
- exploring implementation options
- doing careful edits where you want to review each step
- debugging with you in the loop

### Junie is best for
- “Take this issue/goal and fix it end-to-end”
- “Refactor X across files and keep tests green”
- “Add tests for Y and make them pass”
- “Make docs consistent with codebase”
- “Remove dead code and update references”
- “Automate linting/formatting/test runs, keep output clean”

In other words: **Junie is a task runner + integrator** once the project is stable enough to run checks and verify success.

---

## Why you didn’t reach for Junie earlier (and how to make it natural)

The usual blockers are:

### 1) No reliable verification loop
If there’s no `pytest` (or it’s flaky), an agent can’t confidently “finish” tasks.  
You fixed this: `pytest` now passes quickly.

### 2) Dependency ambiguity
If dependencies live only in your environment (not in metadata), automation has to guess.  
You fixed this by declaring dependencies/extras.

### 3) Unclear “definition of done”
If docs say Parquet but code writes NDJSON, or scripts don’t match CLI flags, agents get stuck.  
You’re actively aligning these.

This is exactly the transition point where Junie becomes useful.

---

## How to start using Junie *in a way that actually helps*

Give Junie **bounded tickets** that have:

- **scope**: files/components involved
- **acceptance criteria**: `pytest` + a command to run
- **constraints**: “Phase 1 outputs NDJSON + provenance only”, “GUI optional”, etc.

Here are good “first Junie tasks” for your repo:

### Task A — align runner script and docs
**Goal:** make `collect_reddit.sh` and docs consistent with the CLI.  
**Acceptance:** `shellcheck` optional; at least script examples match CLI flags; README/runbook updated.

### Task B — add CLI parsing unit tests
**Goal:** add tests for `ph1_cli.py` argument validation and defaults.  
**Acceptance:** `pytest` passes; tests run offline.

### Task C — cancellation behavior test
**Goal:** add a unit test that ensures `collect()` stops when `should_cancel()` becomes `True`.  
**Acceptance:** `pytest` passes; no network access (use fakes/mocks).

### Task D — clean packaging polish
**Goal:** ensure `pip install -e .` works and `pip install -e ".[dev]"` installs pytest only as extra; ensure GUI is `.[gui]`.  
**Acceptance:** installs succeed; `pytest` passes.

These are ideal because they’re concrete and verifiable.

---

## A simple workflow that blends both (and prevents “only Assistant” mode)

1) Use **AI Assistant** to clarify the next ticket and acceptance criteria (5–10 minutes).
2) Hand that ticket to **Junie** to implement end-to-end (code + tests + docs alignment).
3) Use **AI Assistant** to review the result and decide the next ticket.

The key is to **stop using Assistant once the ticket is well-specified**—that’s the handoff moment.

---

## One question to tailor this to your style

When you say “use Junie”, do you mean:

1) *“I want it to autonomously refactor/fix things and add tests”*  
or  
2) *“I want it mainly to run checks and propose diffs, but I still choose each change”*?

If you tell me which mode you prefer, I’ll suggest a short backlog of 5–8 Junie-sized tickets for this project, ordered from safest to most impactful.

Answer: It's more like option 1

## Then the trick is to feed Junie *tickets with guardrails* and let it run

If you want option **(1)** (“autonomously refactor/fix/add tests”), you need to set up a workflow where Junie can:

- make changes freely,
- **prove** the changes are correct (tests),
- and avoid scope creep (constraints).

You’re actually *very close* already: you have `pyproject.toml`, fast `pytest`, and a stable Phase 1 spec.

What’s missing is mainly **a backlog of Junie-sized tasks** and a consistent “definition of done” template.

---

## A “Junie ticket template” that works (copy/paste)

Use this structure whenever you hand a task over:

```text
Goal:
- ...

Scope:
- Files/modules: ...
- Do not touch: ...

Constraints:
- Phase 1 outputs NDJSON + provenance only (no CSV/Parquet).
- GUI remains optional (install via extras).
- No secrets committed.

Acceptance criteria:
- pip install -e ".[dev]" works
- pytest passes
- (optional) CLI smoke run command succeeds (requires local creds)
```

This makes Junie effective because it can operate independently and still know when to stop.

---

## High-impact Junie backlog for *your* project (ordered safest → most autonomous)

### Ticket 1 — Align `collect_reddit.sh` with the actual CLI (safe, high value)
**Why:** scripts/docs mismatch is a classic automation failure.  
**Acceptance:** script examples match CLI flags; no dead flags mentioned.

### Ticket 2 — Add CLI parsing tests (offline)
**Why:** protects your interface while allowing refactors.  
**Acceptance:** tests cover required args, defaults, bad inputs.

### Ticket 3 — Add cancellation test (offline)
**Why:** cancellation is important and easy to regress.  
**Acceptance:** a unit test proves `collect()` stops promptly with `should_cancel()`.

### Ticket 4 — Make “provenance schema” stable and test it (offline)
**Why:** provenance is part of research reproducibility; locking its shape prevents accidental breaking changes.  
**Acceptance:** test asserts required keys exist (`params`, `counts`, timestamps, versions).

### Ticket 5 — Refactor row-mapping into a dedicated module + tests (offline)
**Why:** makes mapping deterministic and testable without PRAW objects.  
**Acceptance:** tests run with lightweight fakes; no network.

### Ticket 6 — Add a `make test` / `make smoke` (or simple shell script) (optional)
**Why:** gives Junie one obvious command to run.  
**Acceptance:** `make test` runs `pytest -q`.

---

## How to “create the moment” where Junie takes over

Instead of continuing to refine interactively, do this:

1) You (with Assistant) pick **one ticket** from the list and finalize the acceptance criteria.
2) Hand that ticket to Junie and **don’t** add new requirements mid-run.
3) Review the output only at the end; if it’s not right, file a follow-up ticket.

This is basically how you’d manage a human contributor—Junie works best the same way.

---

## Suggested first ticket (based on what you’ve shown)

Start with Ticket 1:

**Goal:** Update `collect_reddit.sh` to match `ph1_cli.py` flags and add one canonical usage example.  
**Constraints:** don’t change collector behavior, don’t add time-window flags.  
**Acceptance:** script runs and forwards args unchanged; docs/examples are accurate.

---

## One question to calibrate autonomy

Do you want Junie to be allowed to:
- **add new files** (tests/helpers),
- **refactor module boundaries**, and
- **update docs** as part of the same ticket?

Or do you prefer “code-only” tickets and “docs-only” tickets separately?

Your answer will determine how big each Junie ticket should be.

Answer: I'd try a greater autonomy just to see what happens.

## Great—“greater autonomy” works best if you put bumpers on the bowling lane

If you let Junie run with high autonomy, you’ll get the best results when you give it:

1) **a clear mission**
2) **hard constraints** (things it must not do)
3) **a single verification command** (`pytest`)
4) **a stop condition** (“done when tests pass and docs are consistent”)

You’re already set up for this (fast tests, clean Phase 1 spec, dependencies declared).

---

## A high-autonomy “starter mission” that’s safe and useful

Use a single ticket that allows Junie to touch code *and* docs *and* tests:

### Mission: “Phase 1 cleanup & consistency sweep”
**Goal**
- Make Phase 1 fully consistent with the design: **NDJSON + provenance only**
- Remove dead/unused code
- Ensure CLI/runner script/docs are aligned
- Improve tests where missing

**Constraints (hard)**
- Do **not** add new features (no new CLI flags unless strictly required to fix mismatches)
- Do **not** introduce networked tests (unit tests must run offline)
- Keep GUI optional (install via extras)
- Do not touch or commit secrets

**Acceptance criteria**
- `pip install -e ".[dev]"` succeeds
- `pytest` passes
- `python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 3 --no-include-comments` still works (manual smoke run)

This kind of ticket gives Junie room to “do the right thing” without you micromanaging.

---

## What to expect when you give Junie more autonomy

### Likely good outcomes
- Removes unused modules / duplicated code
- Adds missing tests (CLI parsing, provenance shape, cancellation)
- Fixes doc/script drift
- Simplifies dependency declarations

### Likely “surprises” (not necessarily bad)
- Renames things for clarity
- Moves small functions into new helper modules
- Tightens error handling (more explicit exceptions/messages)
- Updates README/runbook examples to match reality

---

## How to keep autonomy from turning into chaos

### 1) Ask for one PR-style change set at a time
Even if Junie can do a lot, you want changes in **one coherent batch** so you can review.

### 2) Require a “report” at the end
Ask it to output:
- What files changed and why
- How to verify (commands run)
- Any breaking changes (ideally none)

### 3) Keep a rollback point
Before you start, create a safety checkpoint (git branch or commit). Then if you don’t like the outcome, you can reset.

```bash
git checkout -b junie-autonomy-try
git commit -am "Checkpoint before Junie autonomy sweep" || true
```

(If there are untracked files, add them as appropriate before the checkpoint.)

---

## The exact prompt I’d give Junie (copy/paste)

```text
Please do an autonomous consistency sweep for Phase 1.

Goals:
- Ensure Phase 1 outputs are strictly NDJSON + provenance only.
- Remove dead/unused code and fix any duplication that increases maintenance burden.
- Align collect_reddit.sh examples with the actual CLI flags.
- Add/adjust offline unit tests so core behaviors are protected (no network).
- Keep GUI optional (installable via extras).

Constraints:
- Do not add new features unless needed to fix inconsistencies.
- Do not add tests that require Reddit/network access.
- Do not add or commit secrets.

Acceptance criteria:
- pip install -e ".[dev]" works
- pytest passes
- (manual smoke) python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 3 --no-include-comments still works

At the end, provide:
- a summary of changes by file
- commands used to verify
- any follow-up recommendations
```

---

## After the run: how to review quickly (10-minute checklist)

1) `pytest` still green  
2) README + runbook + script examples match the CLI  
3) Phase 1 writes only:
   - `raw/*.ndjson`
   - `logs/*.json`
4) No secrets tracked:
   ```bash
   git ls-files env/.env
   ```

---

If you want, tell me which “autonomy sweep” you’re starting with (Phase 1 only vs. whole repo), and I’ll tighten the constraints so Junie has freedom **without** accidentally expanding scope.

Answer: Can you help me check what Junie did?

## What Junie did (quick, concrete review)

From the project tree + git diff, Junie made **three meaningful changes**:

1) **Deduplicated run-folder naming logic**  
   - Moved the “safe subdir + default run subdir” helpers out of both CLI and GUI into a new module:
   - New file: `src/cl_st1/ph1/naming.py`
   - Updated:
     - `src/cl_st1/ph1/cli/ph1_cli.py` now imports `default_run_subdir`
     - `src/cl_st1/ph1/gui/ph1_gui.py` now imports `default_run_subdir`

2) **Tweaked `collect_reddit.sh` examples**  
   - Updated the “posts only” example to explicitly pass `--no-include-comments` (matches your “posts by default” intent).

3) **Added an offline unit test for collection**  
   - New: `tests/test_collect_offline.py`  
   - It mocks out the Reddit client and verifies:
     - NDJSON outputs exist and contain expected IDs
     - provenance log is written
     - return counts match

Overall: these are all good “autonomy sweep” moves—dedupe + better script accuracy + more test coverage.