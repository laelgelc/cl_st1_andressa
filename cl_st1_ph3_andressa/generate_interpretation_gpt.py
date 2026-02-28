#!/usr/bin/env python3
"""
send_interpretation_prompts_gpt.py

Reads files from interpretation/input (e.g., f1_pos.txt),
sends the ENTIRE file text as a single user prompt to GPT,
and saves GPT's response to interpretation/output with the SAME filename.

Usage:
    # 1) Ensure your API key is available in the environment:
    export OPENAI_API_KEY="<YOUR_API_KEY>"

    # 2) Submit all interpretation prompts (one .txt file per factor pole):
    python send_interpretation_prompts_gpt.py \
        --input interpretation/input \
        --output interpretation/output \
        --model gpt-5.1 \
        --workers 4 \
        --max-output-tokens 9000 \
        --skip-existing \
        --retries 5 \
        --retry-base-sleep 2.0
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# ------------------------------------------------------------
# API
# ------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print(
        "Error: `openai` package not installed in the current environment.\n"
        "Install it into your active project environment (e.g., your conda env) and retry."
    )
    sys.exit(1)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send LMDA interpretation prompts to GPT (no unpacking)."
    )
    parser.add_argument("--input", "-i", required=True, help="Directory containing prompt files.")
    parser.add_argument("--output", "-o", required=True, help="Directory for GPT responses.")
    parser.add_argument("--model", "-m", default="gpt-5.1", help="Model to use (default: gpt-5.1).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=9000, help="Maximum output tokens.")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip prompts whose output file already exists.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of retries for transient API/network failures (default: 5).",
    )
    parser.add_argument(
        "--retry-base-sleep",
        type=float,
        default=2.0,
        help="Base sleep (seconds) for exponential backoff (default: 2.0).",
    )
    return parser.parse_args()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def call_api(*, client: OpenAI, model: str, full_prompt: str, max_output_tokens: int) -> str:
    """
    Sends the ENTIRE prompt file as a single user message.
    """
    response = client.responses.create(
        model=model,
        input=[
            {"role": "user", "content": full_prompt},
        ],
        max_output_tokens=max_output_tokens,
        temperature=0.0,
    )

    out = response.output_text
    if not out:
        raise RuntimeError("API returned empty output.")
    return out


def call_api_with_retries(
        *,
        model: str,
        full_prompt: str,
        max_output_tokens: int,
        retries: int,
        base_sleep: float,
) -> str:
    """
    Retry wrapper with exponential backoff + jitter for transient failures.
    Creates a fresh client per call to avoid any thread-safety assumptions.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return call_api(
                client=client,
                model=model,
                full_prompt=full_prompt,
                max_output_tokens=max_output_tokens,
            )
        except Exception as e:
            last_err = e
            if attempt >= retries:
                break

            sleep_s = base_sleep * (2 ** attempt)
            sleep_s = sleep_s * (0.8 + 0.4 * random.random())  # jitter in [0.8, 1.2]
            print(f"[WARN] Attempt {attempt + 1}/{retries} failed: {e} — retrying in {sleep_s:.1f}s")
            time.sleep(sleep_s)

    raise RuntimeError(f"API call failed after {retries + 1} attempts: {last_err}") from last_err


# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(
        *,
        path: Path,
        outpath: Path,
        model: str,
        max_tokens: int,
        retries: int,
        base_sleep: float,
) -> bool:
    try:
        print(f"[WORKER] Reading {path.name}")
        full_prompt = read_text(path).strip()
        if not full_prompt:
            raise ValueError("Prompt file is empty (after stripping).")

        print(f"[WORKER] Sending to GPT: {path.name}")
        result = call_api_with_retries(
            model=model,
            full_prompt=full_prompt,
            max_output_tokens=max_tokens,
            retries=retries,
            base_sleep=base_sleep,
        )

        write_text(outpath, result)
        print(f"[WORKER] Saved → {outpath}")
        return True

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main() -> None:
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"ERROR: input directory does not exist or is not a directory: {input_dir}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: OPENAI_API_KEY not set in environment.")

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No prompt files found.")
        sys.exit(0)

    tasks: list[tuple[Path, Path]] = []
    for f in files:
        outpath = output_dir / f.name
        if args.skip_existing and outpath.exists():
            continue
        tasks.append((f, outpath))

    if not tasks:
        print("Nothing to do (all outputs exist).")
        sys.exit(0)

    print(f"Submitting {len(tasks)} prompts using {args.workers} workers…")

    ok = 0
    failed: list[str] = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                process_prompt,
                path=in_path,
                outpath=out_path,
                model=args.model,
                max_tokens=args.max_output_tokens,
                retries=args.retries,
                base_sleep=args.retry_base_sleep,
            )
            for in_path, out_path in tasks
        ]

        for fut in as_completed(futures):
            if fut.result():
                ok += 1
            else:
                failed.append("unknown")  # detailed errors are already printed

    print(f"\nDone. Succeeded: {ok}/{len(tasks)}")
    if ok != len(tasks):
        raise SystemExit("ERROR: some prompts failed—see log above.")


if __name__ == "__main__":
    main()