# Phase 1 Runbook — Reddit Data Collection (Lab Team)

This document is the **operational guide** for running Phase 1 data collection in a consistent, reproducible, and ethically responsible way.

## 0) Scope and principles (read first)

- We collect **public Reddit data** using the official API (PRAW) and follow Reddit ToS and subreddit rules.
- The study focus is **posts (submissions)**. The pipeline can optionally include **comments**, but only enable this when needed.
- Treat collected text as **sensitive**. Do not share raw dumps outside the approved team/institution workflow.
- Do not commit secrets (`env/.env`) to git.

---

## 1) Prerequisites

### 1.1 Reddit API credentials
You need a Reddit API “script” application and the following variables available to the program:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `USER_AGENT` (descriptive; include project name and contact)

Store these locally in `env/.env` (see `env/.env.template`), or set them as environment variables in your shell/session.

### 1.2 Environment and install

From the repository root, install the package in editable mode:

```bash
pip install -e .
```

For development/testing (recommended for anyone making changes):

```bash
pip install -e ".[dev]"
pytest
```

Optional GUI:

```bash
pip install -e ".[gui]"
```

---

## 2) What the collector writes (outputs)

Each run writes into an output directory.

### 2.1 Output directory layout (Phase 1)

Within the chosen run directory:

- `raw/`
  - `reddit_submissions.ndjson`
  - `reddit_comments.ndjson` (only if comments are enabled)
- `logs/`
  - `ph1_run_<timestamp>.json` (provenance: parameters, versions, counts, timestamps)

**Directory creation is automatic**: the collector creates `raw/` and `logs/` if missing.

**Note:** Phase 1 does **not** write normalized tables (CSV/Parquet). Any tabular exports belong to Phase 2+.

### 2.2 Filename/Folder naming scheme for runs (auto-naming)

If you do not provide an explicit `--out-dir` (CLI), the run is stored under `data/ph1/` with an auto-generated folder name:

```text
data/ph1/<listing>_<limit>_<subreddits>_<UTCtimestamp>/
```

Where:
- `<listing>` is `new` or `top`
- `<limit>` is the per-subreddit limit (N)
- `<subreddits>` is the subreddit list joined with `+` and sanitized for filesystem safety
- `<UTCtimestamp>` is `YYYYMMDD_HHMMSS` in UTC

Example:

```text
data/ph1/new_1000_loneliness_20260208_121600/
```

---

## 3) Output directory overrides (team standard)

- Use `--out-dir` to fully control the output path (disables auto-naming).

Example:

```bash
python -m cl_st1.ph1.cli.ph1_cli \
  -s loneliness \
  --listing new \
  --per-subreddit-limit 1000 \
  --no-include-comments \
  --out-dir data/ph1/custom_runs/new_1000_loneliness
```

---

## 4) Standard run recipes (CLI)

All commands below are run from the repository root.

### 4.1 Quick sanity run (posts only)
Use a small limit to validate credentials and output formatting:

```bash
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 10 --no-include-comments
```

### 4.2 Collect N most recent posts from `new` (posts only; recommended default)

```bash
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 1000 --no-include-comments
```

### 4.3 Collect N posts from `top` (all time) (posts only)

```bash
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing top --per-subreddit-limit 500 --no-include-comments
```

### 4.4 Include comments (only if needed)

```bash
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 200 --include-comments --comments-limit-per-post 200
```

### 4.5 Force an explicit output directory

```bash
python -m cl_st1.ph1.cli.ph1_cli -s loneliness --listing new --per-subreddit-limit 1000 --out-dir data/ph1/my_run_001
```

---

## 5) EC2 execution pattern (team standard)

This phase can be run on a dedicated EC2 instance. Outputs are written to the instance’s attached **EBS volume**.

### 5.1 Stop-on-success (default)
Our standard is **stop on success**:

- If the collector exits successfully (exit code `0`), the instance should be stopped automatically.
- If the collector fails (non-zero exit), the instance should remain running so a team member can SSH in and debug.

This reduces cost while preserving fast debugging.

### 5.2 Stop-always (optional cost-control mode)
For unattended overnight runs, it can be acceptable to stop the instance **even on failure**, to avoid cost leaks.

Use stop-always only when:
- the job is stable,
- logs are written to disk,
- the team accepts debugging after restart.

### 5.3 Runner script (`collect_reddit.sh`) usage

The repository includes an EC2 runner script that:
- activates the conda environment,
- runs the collector via `python -u -m cl_st1.ph1.cli.ph1_cli ...`,
- optionally stops the EC2 instance based on exit code and tag safeguards.

Run from the repository root:

```bash
chmod +x collect_reddit.sh
```

Posts only (recommended default), stop on success:

```bash
nohup ./collect_reddit.sh -s loneliness --listing new --per-subreddit-limit 1000 --no-include-comments > process_output.log 2>&1 &
```

Include comments, stop always:

```bash
STOP_ALWAYS=1 nohup ./collect_reddit.sh -s loneliness --include-comments --comments-limit-per-post 200 > process_output.log 2>&1 &
```

Explicit output directory:

```bash
nohup ./collect_reddit.sh -s loneliness --out-dir data/ph1/my_run_001 > process_output.log 2>&1 &
```

### 5.4 Auto-stop safeguard: instance tag + IMDS setting
The EC2 runner script (`collect_reddit.sh`) can be configured to stop the instance only if it has a specific tag:

- Tag key: `AutoStop`
- Tag value: `true`

This prevents accidental stops if the script is run on the wrong instance.

#### Add the tag in the AWS Console
1. EC2 Console → **Instances**
2. Select the instance
3. **Tags** tab → **Manage tags**
4. Add:
   - Key: `AutoStop`
   - Value: `true`
5. Save

#### Important: enable “Instance metadata tags” (IMDS)
The script checks the tag via IMDS. You must enable instance tags in metadata:

- EC2 Console → **Instances** → select instance
- **Actions** → **Instance settings** → **Modify instance metadata options**
- Enable the option that allows **instance tags in metadata** (wording varies)
- Save

If tags-in-IMDS is not enabled, the script will refuse to stop the instance (as a safety measure).

### 5.4 Data safety (minimum bar)
EBS persistence across stops is usually sufficient for day-to-day work, but it is not a backup.

After any major successful run:
- take an **EBS snapshot**, or
- export the run folder to durable storage (if/when the team adopts it).

### 5.5 Repository hygiene (what gets pushed)
Do **not** commit secrets or raw corpora to git.

Recommended to push:
- code changes
- documentation updates
- run parameters and provenance summaries (if appropriate)

Raw exports (NDJSON with text) should remain on EBS (or other approved storage) unless the lab has a specific policy for storing corpora in version control.

---

## 6) Team “Do/Don’t” checklist (ethics + hygiene)

### Do
- Use descriptive `USER_AGENT`.
- Start with posts-only unless comments are required.
- Keep a record of each run (output folder + provenance log).
- Treat raw text files as sensitive internal data.

### Don’t
- Don’t commit `env/.env` or any secrets.
- Don’t publish raw NDJSON dumps.
- Don’t scrape via HTML pages when the API is available.

---

## 7) Troubleshooting

### “No module named cl_st1”
Make sure you installed editable:

```bash
pip install -e .
```

### “pytest: command not found”
Install dev dependencies:

```bash
pip install -e ".[dev]"
```

### Authentication errors
- Verify credentials are present and correct.
- Ensure your `env/.env` is loaded by your configuration logic, or export variables in the shell environment.

### Runs are slow / rate limits
- Lower `--per-subreddit-limit` and/or `--comments-limit-per-post` for test runs.
- Expect backoff/retry behavior on transient errors.

### Output files exist but are empty
- If using `new` or `top`, an empty output usually indicates the run was cancelled early or the run ended before any items were yielded (rare).
- Check the provenance JSON under `logs/` for collected counts.

---

## 8) Provenance and reproducibility

For every run, capture:
- the output folder path
- the provenance JSON file under `logs/`
- the CLI command used (copy/paste into a lab notebook)

This is essential for reproducible corpora.
