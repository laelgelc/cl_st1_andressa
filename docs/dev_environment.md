# Developer Environment — Setup & Workflow

This document describes the **recommended development workflow** for the lab team (CLI + future GUI).

## 1) Python environment

Use the project’s conda environment (as configured by the team). Activate it before running anything.

## 2) Install the project (editable)

From the repository root:

```
bash pip install -e .
```

Why: this makes `cl_st1` importable everywhere (terminal runs, GUI runs, tests) without relying on `PYTHONPATH=src`.

## 3) Verify imports

```
bash python -c "import cl_st1; print('OK:', cl_st1.**file**)"
```

## 4) Run the CLI

Show help:

```
bash python -m cl_st1.ph1.cli.ph1_cli --help
```

Typical run:

```
bash python -m cl_st1.ph1.cli.ph1_cli -s loneliness --year 2024 --no-include-comments
```

## 5) Working with PyCharm

Recommended:
- Interpreter: select the conda env for this project
- Run configurations:
    - Module run: `cl_st1.ph1.cli.ph1_cli`
    - Working directory: repository root

Because we use editable install, you generally **do not** need to set `PYTHONPATH`.

## 6) Secrets / credentials

- Copy `env/.env.template` to the expected local `.env` location used by the project.
- Never commit `.env` (it should be in `.gitignore`).

Use placeholders in documentation and examples—never paste real credentials into chat, tickets, or commits.

## 7) Data directories

Outputs are written under `data/ph1/...` (or a configured output dir). Treat raw exports as sensitive. Avoid syncing raw corpora to public locations.

## 8) Common pitfalls

### Import errors after pulling changes
Re-run:

```
bash pip install -e .
```

### Mixed environments
If something behaves “weirdly”, confirm:
- PyCharm interpreter points to the same conda env you’re using in the terminal.
- `which python` points to the env’s Python.
