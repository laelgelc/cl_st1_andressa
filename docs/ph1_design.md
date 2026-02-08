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

### 2.2 Outputs
Phase 1 outputs are **raw-first**:

- Raw NDJSON (append-only):
    - `raw/reddit_submissions.ndjson`
    - `raw/reddit_comments.ndjson` (only if comments enabled)
- Provenance log:
    - `logs/ph1_run_<timestamp>.json`

Optional output (allowed but not required by this streamlined Phase 1 spec):
- Normalized tables:
    - `tables/posts.parquet`
    - `tables/comments.parquet`

### 2.3 Explicitly out of scope (Phase 1)
- language identification / language filtering
- deduplication
- cleaning / normalization beyond selecting a stable set of raw fields
- sampling strategies beyond “listing + limit”
- analytics / LMDA feature extraction

---

## 3. Important behavioral note (methodology)

Using a listing like `new` with `limit=N` means:

> the collector requests **up to N of the most recent posts** from that listing, then stores them.

It does **not** guarantee coverage of an arbitrary historical time window. If historical coverage is needed, that becomes a Phase 2+ concern (different retrieval strategy and/or larger scans) and must be documented accordingly.

---

## 4. Architecture

### 4.1 Modules
- `src/cl_st1/common/`
    - `config.py`: loads credentials (expects `env/.env` locally), validates required vars
    - `storage.py`: creates output directories, appends NDJSON, writes provenance (and optionally Parquet)
    - `log.py`: logging helpers (optional)
- `src/cl_st1/ph1/`
    - `reddit_client.py`: constructs authenticated PRAW client
    - `collect_service.py`: core collection orchestration
    - `cli/ph1_cli.py`: CLI wrapper around the service
    - `gui/ph1_gui.py`: PySide6 GUI wrapper around the service

### 4.2 Service contract (recommended for Phase 1)
The service should accept a small set of stable parameters that both CLI and GUI can provide:

- `subreddits`
- `listing` (e.g., `new`, `top`)
- `limit_per_subreddit`
- `include_comments`, `comments_limit_per_post`
- `out_dir`
- callbacks: `progress(msg)`, `counts(posts, comments)`
- cancellation: `should_cancel()`

Time-window filtering parameters (`after_utc`, `before_utc`) are considered **optional/legacy** and should not be required for Phase 1 streamlined collection.

---

## 5. Data model (raw records)

### 5.1 Submissions (posts)
Store a consistent subset of fields for downstream processing:

- `id`
- `subreddit`
- `created_utc`
- `author` (may be `None`)
- `title`
- `selftext`
- `score`
- `num_comments`
- `url`
- `permalink`
- `over_18`
- `removed_by_category`

### 5.2 Comments (optional)
- `id`
- `link_id` (submission id)
- `parent_id`
- `subreddit`
- `created_utc`
- `author` (may be `None`)
- `body`
- `score`
- `permalink`
- `removed_by_category`

---

## 6. Provenance (required)

Every run must write a provenance JSON containing at least:
- timestamps (`started_at`, `finished_at`)
- run parameters:
    - subreddits, listing, limits, include_comments, out_dir
- counts:
    - number of posts/comments collected
- versions (useful for reproducibility):
    - python, praw, pandas, pyarrow (if used)

This provenance record is the foundation for transparent reporting.

---

## 7. Rate limits, retries, etiquette

- Use descriptive `USER_AGENT`.
- Respect Reddit ToS and API rate limits.
- Retry transient failures with capped exponential backoff.
- Prefer continuing collection for recoverable item-level errors rather than failing the entire run.

---

## 8. GUI slice (PySide6)

### 8.1 GUI inputs (aligned to streamlined Phase 1)
- Subreddits (comma-separated)
- Listing selector (`new`, `top`, …)
- Limit per subreddit (N)
- Include comments checkbox + limit per post
- Output directory (read-only default, or selectable in future)
- Start / Cancel
- Progress log + counters

### 8.2 Threading / cancellation
- Run collection in a background worker thread.
- Cancel button sets a flag; worker passes `should_cancel()` to the service.

---

## 9. CLI slice (aligned to streamlined Phase 1)

Required:
- `--subreddits`
- `--listing` (default `new`)
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