# Phase 1 Design — Data Collection (Reddit)

This document specifies the minimal viable slice (MVS) for Phase 1, with implementation focused in Junie (PySide6 GUI-first). Scope: collect public Reddit submissions and comments relevant to loneliness, persist raw and normalized data, and provide a simple GUI (primary) and CLI (secondary) entry point.

## Current implementation status (living section)

Implemented:
- CLI entry point under `src/cl_st1/ph1/cli/ph1_cli.py`.
- Time window selection supports:
  - per-year collection (`--year YYYY`), and
  - custom windows (`--after-utc/--before-utc` or `--after-date/--before-date`).
- Default collection mode is **posts only**; comments are optional (`--include-comments`).
- Auto-named output folders when `--out-dir` is omitted:
  - per-year: `data/ph1/<YEAR>_<SUBREDDITS>`
  - window: `data/ph1/window_<START>_to_<END|open>_<SUBREDDITS>`
- Provenance logs and raw/tables outputs are written under the run output directory.
- GUI entry point present under `src/cl_st1/ph1/gui/ph1_gui.py` (PySide6):
  - year mode + date-range mode time window UX (UTC), internally converted to epoch seconds for collection/provenance
  - background worker thread with progress + counts updates
  - cancel button is implemented as a best-effort UI cancellation (service-side cancellation may be improved)

Planned next:
- Improve cancellation semantics end-to-end (propagate a cancel flag into the service loops and stop promptly).
- GUI input validation polish (clearer errors; disable irrelevant fields; sensible defaults).
- Ensure PySide6 is available in the team environment configuration for GUI runs.
- Tests for helpers and CLI parsing (time window and output naming).

## 1. Objectives

- Collect submissions (and optional comments) from target subreddits within a time window.
- Persist:
  - Raw NDJSON for archival/provenance.
  - Normalized tables (Parquet/CSV) for downstream processing.
- Provide two entry points (GUI first):
  - GUI (PySide6): user-friendly run configuration, background execution, status.
  - CLI: batch-friendly wrapper reusing the same service.
- Log provenance (config used, timestamps, sources) and respect API limits/ToS.

## 2. Scope (MVS)

Inputs:
- Subreddit list (comma-separated).
- Time window (user-facing):
  - **Either**: calendar `year` in UTC
  - **Or**: `after_date` (UTC) and optional `before_date` (UTC)
  - (Advanced/automation) `after_utc` / `before_utc` epoch seconds
- Sort: new (default) or top.
- Include comments: boolean + comments_limit_per_post.
- Per-subreddit limit: optional cap.

Outputs:
- data/ph1/raw/ reddit_submissions.ndjson
- data/ph1/raw/ reddit_comments.ndjson (optional)
- data/ph1/tables/ posts.parquet
- data/ph1/tables/ comments.parquet (optional)
- data/ph1/logs/ ph1_run_YYYYMMDD_HHMMSS.json (provenance)

Out of scope for Phase 1: cleaning, language ID, de-dup, analytics.

## 3. Architecture

- src/cl_st1/common/
  - config.py: Load env/.env with python-dotenv; expose get_settings() with REDDIT_CLIENT_ID/SECRET and USER_AGENT. Validate presence.
  - storage.py: Ensure dirs, write NDJSON (append-friendly) and Parquet (batch write), simple path helpers under data/ph1/.
  - log.py: get_logger() returning a logger that can write to console/file, and an adapter to emit messages into the GUI.

- src/cl_st1/ph1/
  - reddit_client.py: get_reddit() returning an authenticated PRAW client using settings.
  - collect_service.py:
    - fetch_submissions(subreddit, sort, after/before, limit)
    - fetch_comments(submission, limit_per_post)
    - normalize to dict rows; periodic flush to NDJSON; finalize Parquet.
    - backoff/retry with capped exponential strategy.
    - progress callbacks: on_progress(msg), on_counts(posts, comments).
  - gui/ph1_gui.py (PySide6):
    - Form inputs; Start/Cancel actions.
    - Background worker (QThread/QRunnable) that calls collect_service.collect().
    - Signals for progress lines, counts, completion, and errors.
    - **Time window UX:** year mode and date-range mode; internally convert to epoch seconds for collection/provenance.
  - cli/ph1_cli.py: argparse to parse flags → call collect_service.collect().

## 4. Data Model

Posts (submissions):
- id, subreddit, created_utc, author, title, selftext, score, num_comments, url, permalink, over_18, removed_by_category

Comments:
- id, link_id (submission id), parent_id, subreddit, created_utc, author, body, score, permalink, removed_by_category

Notes:
- created_utc is epoch seconds (int). Author may be None for deleted accounts.

## 5. I/O and Paths

Base dir: data/ph1/
- raw/: reddit_submissions.ndjson, reddit_comments.ndjson
- tables/: posts.parquet, comments.parquet
- logs/: ph1_run_{timestamp}.json

Ensure directories up front. NDJSON is line-delimited JSON, one object per line. Parquet written once at the end of the run from in-memory buffers (bounded by per_subreddit_limit in MVS).

## 6. Configuration

- Secrets (env/.env; not committed):
  - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
  - USER_AGENT (e.g., cl_st1_loneliness/1.0 (by u/your_username))
- Runtime (GUI/CLI parameters):
  - subreddits: list[str]
  - sort: new|top (default=new)
  - per_subreddit_limit: int|None (default=1000)
  - include_comments: bool (default=true)
  - comments_limit_per_post: int (default=300)
  - after_utc: int (required; derived from year/after_date in GUI/CLI)
  - before_utc: int|None
  - out_dir: data/ph1 (default)

Provenance JSON records parameters, start/end times, counts, and package versions (python, praw, pandas, pyarrow).

## 7. Rate Limits, Retries, Etiquette

- Descriptive user_agent required.
- Exponential backoff on exceptions: 1s, 2s, 4s, … capped at 60s; reset on success.
- Optional per-request sleep (e.g., 0.5–1.0s).
- Continue on item-level errors; log and proceed.

## 8. GUI Slice (PySide6 with Junie)

UI elements:
- Inputs:
  - QLineEdit: Subreddits (comma-separated)
  - Time window (UTC): Year mode and Date-range mode
    - Year mode: QSpinBox (year)
    - Date-range mode: QDateEdit/QDateTimeEdit (after date; before date optional)
    - (Optional display) resolved after_utc/before_utc epoch seconds (read-only) for transparency/provenance
  - QComboBox: Sort (new/top)
  - QCheckBox + QSpinBox: Include comments + limit per post
  - QSpinBox: Per-subreddit limit
  - QLabel: Output directory (read-only; defaults to data/ph1)
- Actions:
  - QPushButton: Start (disabled while running)
  - QPushButton: Cancel (enabled while running)
- Status:
  - QPlainTextEdit: log/progress lines (append-only)
  - QLabel: counters (posts, comments)
  - QProgressBar: indeterminate (busy) during run

Threading:
- Worker in QThread/QRunnable; signals:
  - progress(str), counts(int, int), finished(success: bool), error(str)
- Cancel via a shared flag checked between API calls.

Accessibility and UX:
- Disable inputs on run; re-enable on finish/cancel.
- Validate inputs (non-empty subreddits; after_utc numeric; sensible limits) before starting.

## 9. CLI Slice

Args:
- -s/--subreddits
- --sort
- --per-subreddit-limit
- --include-comments / --no-include-comments
- --comments-limit-per-post

Time window (choose one mode):
- --year
- --after-date / --before-date
- --after-utc / --before-utc

Output location:
- --out-dir
- --out-dir-base
- --run-subdir

Exit 0 on success; non-zero on fatal error. Logs to stdout + file in logs/.

## 10. Testing

- Unit tests for:
  - common/config: env loading (uses env/.env), missing creds → friendly error
  - common/storage: directory creation, NDJSON append, Parquet write
  - ph1/collect_service: normalization helpers (using lightweight fakes)
- Smoke test (manual or skipped in CI):
  - Tiny run: 3 posts, 3 comments per post against a test subreddit; asserts files exist and contain rows.

## 11. Security & Ethics

- Never commit env/.env. Keep .env.template committed.
- Respect Reddit ToS and subreddit rules.
- Consider a future option to hash author ids.

## 12. Roadmap (GUI-first increments)

- v0.1: GUI form + background worker + progress; NDJSON + Parquet; provenance file.
- v0.2: Cancel support, better validation, per-subreddit delay option.
- v0.3: Saved presets; select output directory; basic error dialogs.
- v0.4: CLI parity with GUI options.

## 13. Done Definition (for this slice)

- GUI can run a collection with user-specified subreddits and time window.
- Files created under data/ph1/{raw,tables,logs}.
- Provenance JSON written; run is reproducible.
- Basic unit tests pass; manual smoke run succeeds with tiny limits.