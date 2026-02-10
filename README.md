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
