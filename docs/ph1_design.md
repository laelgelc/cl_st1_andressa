# Phase 1 Design — Reddit Data Collection (Streamlined)

This document defines the **minimal viable slice (MVS)** for Phase 1.
Phase 1’s job is to **collect raw public Reddit data reproducibly** (with provenance) and **not** to perform data wrangling/cleaning. Those steps belong to later phases.

**Guiding principle:** Phase 1 should be simple, robust, and transparent about what was collected.

---

## Current implementation status (living section)

Implemented in the repository:
- Shared service: `src/cl_st1/ph1/collect_service.py`
    - Collects posts and optionally comments.
    - Writes raw NDJSON incrementally.
    - Writes provenance JSON.
    - Supports best-effort cancellation via `should_cancel()` callback.
    - (Currently also writes Parquet tables at end-of-run.)
- CLI entry point: `src/cl_st1/ph1/cli/ph1_cli.py`
- GUI entry point: `src/cl_st1/ph1/gui/ph1_gui.py` (PySide6)
- Unit tests exist for time-window parsing semantics (legacy behavior) under `tests/ph1/`.

**Note:** Some features currently implemented (time-window inputs; Parquet tables) were added earlier. This streamlined spec treats them as **optional/legacy** and prioritizes the simpler “listing + limit” collection mode going forward.

Planned next (to fully match the streamlined spec):
- Align CLI/GUI UX to the streamlined inputs (listing + limit); keep time-window inputs as optional/advanced or move to Phase 2.
- Decide whether Parquet belongs in Phase 1 (optional) or moves to Phase 2 (recommended for large runs).

---

## 1. Objective (Phase 1)

Collect a specified number of **public** Reddit submissions from a specified subreddit listing (and optionally comments), while:
- respecting Reddit API rules and rate limits,
- producing reproducible output with provenance,
- keeping secrets out of version control.

---

## 2. Scope (MVS)

### 2.1 Inputs (user-facing)
Required:
- `subreddits`: list of subreddit names (e.g., `loneliness`)
- `listing`: which listing to pull from (default: `new`)
- `limit_per_subreddit`: number of posts to fetch from that listing (N)

Optional:
- `include_comments`: boolean (default: **false**; study focus is posts)
- `comments_limit_per_post`: integer cap if comments are enabled
- `out_dir`: output directory (default: `data/ph1` or an auto-named subfolder)

#### Supported `listing` values (Phase 1)
Phase 1 supports the following listings via PRAW:

- `new` (default): fetches up to N **most recent** posts in the subreddit (newest → older as you iterate).
- `top`: fetches up to N **top-scoring** posts in the subreddit according to Reddit’s ranking.
    - Phase 1 uses a fixed `time_filter="all"` for `top` (i.e., top posts of all time).

Notes:
- These listings are **server-side orderings**. They are not guaranteed to provide complete historical coverage for a chosen time window.
- `limit_per_subreddit=N` controls the **maximum number of items requested from the listing**, not the number that will necessarily match any later filters.

---

## 3. Important behavioral note (methodology)

Using a listing like `new` with `limit=N` means:

> the collector requests **up to N of the most recent posts** from that listing, then stores them.

Using `top` with `limit=N` means:

> the collector requests **up to N top-ranked posts** (with `time_filter="all"`), then stores them.

This does **not** guarantee coverage of an arbitrary historical time window. If historical coverage is needed, that becomes a Phase 2+ concern (different retrieval strategy and/or larger scans) and must be documented accordingly.

---

## 4. Architecture

### 4.2 Service contract (recommended for Phase 1)
The service should accept a small set of stable parameters that both CLI and GUI can provide:

- `subreddits`
- `listing` (supported: `new`, `top`)
- `limit_per_subreddit`
- `include_comments`, `comments_limit_per_post`
- `out_dir`
- callbacks: `progress(msg)`, `counts(posts, comments)`
- cancellation: `should_cancel()`

Time-window filtering parameters (`after_utc`, `before_utc`) are considered **optional/legacy** and should not be required for Phase 1 streamlined collection.

---

## 8. GUI slice (PySide6)

### 8.1 GUI inputs (aligned to streamlined Phase 1)
- Subreddits (comma-separated)
- Listing selector (`new`, `top`)
    - `top` uses `time_filter="all"` in Phase 1
- Limit per subreddit (N)
- Include comments checkbox + limit per post
- Output directory (read-only default, or selectable in future)
- Start / Cancel
- Progress log + counters

---

## 9. CLI slice (aligned to streamlined Phase 1)

Required:
- `--subreddits`
- `--listing` (default `new`; supported: `new`, `top`)
- `--per-subreddit-limit`

Optional:
- `--include-comments / --no-include-comments`
- `--comments-limit-per-post`
- `--out-dir` (or auto naming via base/subdir if desired)

---

## 10. Testing (Phase 1)

### Unit tests (no network)
- CLI parsing logic (listing, limits, argument validation)
- storage helpers (directory creation; NDJSON append)
- normalization helpers (row-shape correctness with lightweight fakes)
- cancellation behavior (service stops promptly when `should_cancel()` becomes true)

### Smoke tests (manual; may touch network)
- Tiny run (e.g., `limit=3`, comments disabled) ensures:
    - output directories created
    - NDJSON contains expected number of rows
    - provenance file written

---

## 11. Security & ethics

- Do not commit secrets (`env/.env`).
- Treat raw text as sensitive research material.
- Respect Reddit and subreddit rules.
- Prefer publishing derived outputs rather than raw corpora.

---

## 12. Done definition (Phase 1 streamlined)
Phase 1 is “done” when:
- CLI and GUI can collect N posts from a chosen listing for specified subreddits.
- Raw NDJSON and provenance are written to a run folder.
- Cancellation works end-to-end.
- Unit tests pass and a tiny manual smoke run succeeds.