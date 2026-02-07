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

## Phase 1 - Data Collection
1. Goal
- Collect Reddit submissions/comments (public data) relevant to loneliness.

2. Outputs
- Raw JSON (NDJSON).
- Normalised tables (Parquet/CSV).
- Provenance logs.

3. Entry points
- CLI: src/cl_st1/ph1/cli/ph1_cli.py
- GUI: src/cl_st1/ph1/gui/ph1_gui.py