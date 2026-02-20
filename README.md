# Corpus Linguistics - Study 1 - Andressa

This project is organised as a multi-phase pipeline.

## Repository layout

- src/cl_st1/
  - common/
  - ph1/
- docs/
- data/
  - ph1/
- config/
- env/
- tests/
  - ph1/

## Documentation
- Phase 1 design: docs/ph1_design.md
- Phase 1 runbook (how to collect data): docs/ph1_runbook.md
- Dev environment setup: docs/dev_environment.md

## Install

From the repository root:

### Runtime (CLI/service)
Installs the Phase 1 collector runtime dependencies:

```
pip install -e .
```

### Development / tests (recommended for contributors)
Installs runtime dependencies plus test tooling:

```
pip install -e ".[dev]"
pytest
```

### Optional GUI
The GUI requires PySide6. Install it via the optional extra:

```
pip install -e ".[gui]"
python -m cl_st1.ph1.gui.ph1_gui
```

To install everything (tests + GUI):

```
pip install -e ".[dev,gui]"
```

## Quick start (Phase 1 CLI)

1) Create your local credentials file:

```
cp env/.env.template env/.env
```

2) Fill in `env/.env` with your Reddit API credentials (do not commit this file).

3) Run a tiny collection (posts only):

```
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 3 --no-include-comments
```

Outputs will be written under `data/ph1/` (raw NDJSON + provenance logs).

## Phase 1 - Data Collection
1. Goal
- Collect Reddit submissions/comments (public data) relevant to loneliness.

2. Outputs
- Raw JSON (NDJSON).
- Provenance logs.

3. Entry points
- CLI: src/cl_st1/ph1/cli/ph1_cli.py
- GUI: src/cl_st1/ph1/gui/ph1_gui.py

## Phase 2 - Data Wrangling for human-authored Reddit posts subcorpus compilation

**Notebook:** `cl_st1_ph2_andressa/cl_st1_ph2_andressa.ipynb`

### Goal
Compile a cleaned subcorpus of **human-authored Reddit posts** from Phase 1 submissions by:
- removing empty/duplicate/very short texts,
- filtering non-target content and non-English posts (with explicit exceptions),
- detecting and collapsing near-duplicate “template” posts,
- adding derived columns for downstream corpus analysis,
- exporting curated datasets for analysis and manual inspection.

### Inputs
- Phase 1 submissions (NDJSON) under: `data/ph1/**/reddit_submissions.ndjson`

### Procedure (high level)
1) **Consolidate Phase 1 exports** into a single posts table and keep only rows with non-empty `selftext`.
2) **Exact de-duplication** on `selftext` (keep first occurrence).
3) **Remove short posts**: drop rows where `selftext` has fewer than **10 words**.
4) **Identify likely non-relevant posts** by searching for keywords (`template`, `agenda`, `discord`) and export matches for review.
5) **Manually drop selected IDs** identified as irrelevant during review.
6) **Language identification**: add a `language` column and keep English (`en`) posts, with a small allow-list of non-English exceptions kept by ID.
7) **Export cleaned dataset** (“human Reddit posts”) as NDJSON + XLSX.
8) **Near-duplicate (template) handling**:
  - detect template-like near-duplicates via text similarity,
  - cluster near-duplicate pairs into “template families”,
  - keep one representative per family (earliest by `created_utc`) and drop the rest,
  - export the updated dataset (“human Reddit posts v2”).
9) **Content curation**: drop specific subreddits deemed out of scope for the study.
10) **Add derived columns**:
- `created_utc_datetime` (UTC timestamp),
- `selftext_word_count`.
11) **Outlier removal (IQR rule)** on `selftext_word_count` and export a “no outliers” dataset.

### Outputs (written under `data/ph2/`)
**Intermediate / review exports**
- `data/ph2/reddit_posts_id_author_selftext.xlsx` (ID/author/selftext for corpus work; overwritten as cleaning progresses)
- `data/ph2/reddit_posts_selftext_template_agenda_or_discord.xlsx` (rows flagged by keyword match for inspection)

**Cleaned datasets**
- `data/ph2/human_reddit_posts.ndjson` and `data/ph2/human_reddit_posts.xlsx`  
  Cleaned posts after: non-empty `selftext`, exact de-duplication, short-text removal, manual ID drops, and language filtering.
- `data/ph2/human_reddit_posts_2.ndjson` and `data/ph2/human_reddit_posts_2.xlsx`  
  Further cleaned after near-duplicate/template collapsing (one representative per template family) and subreddit filtering.
- `data/ph2/human_reddit_posts_2_no_outliers.ndjson` and `data/ph2/human_reddit_posts_2_no_outliers.xlsx`  
  Final dataset after removing `selftext_word_count` outliers using the IQR rule.

### Notes / reproducibility
- Phase 2 is currently implemented as a notebook workflow; outputs are deterministic given the Phase 1 NDJSON inputs plus the explicit “manual drop” ID list and non-English exception IDs recorded in the notebook.
- If you re-run Phase 1 collection (new data), expect Phase 2 row counts to change accordingly.

## Phase 3 
