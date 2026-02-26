#!/usr/bin/env python3
"""
send_interpretation_prompts_gpt.py

Reads files from interpretation/input (e.g., f1_pos.txt),
sends the ENTIRE file text as a single user prompt to GPT,
and saves GPT's response to interpretation/output with the SAME filename.

Usage:
    python send_interpretation_prompts_gpt.py \
        --input interpretation/input \
        --output interpretation/output \
        --model gpt-5.1 \
        --workers 4
"""

import argparse
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------------------
# API
# ------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: Install with: pip install openai")
    sys.exit(1)

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send LMDA interpretation prompts to GPT (no unpacking)."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing prompt files."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Directory for GPT responses."
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-5.1",
        help="Model to use (default: gpt-5.1)."
    )
    parser.add_argument(
        "--max-output-tokens", "-t",
        type=int,
        default=9000,
        help="Maximum output tokens."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers."
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


def call_api(client: OpenAI, model: str, full_prompt: str, max_output_tokens: int) -> str:
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

# ------------------------------------------------------------
# Worker
# ------------------------------------------------------------
def process_prompt(
    path: Path,
    output_dir: Path,
    client: OpenAI,
    model: str,
    max_tokens: int,
):

    try:
        print(f"[WORKER] Reading {path.name}")
        full_prompt = read_text(path)

        print(f"[WORKER] Sending to GPT: {path.name}")
        result = call_api(
            client=client,
            model=model,
            full_prompt=full_prompt,
            max_output_tokens=max_tokens,
        )

        outpath = output_dir / path.name  # SAME name
        write_text(outpath, result)
        print(f"[WORKER] Saved → {outpath}")

        return True

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No prompt files found.")
        sys.exit(0)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"Submitting {len(files)} prompts using {args.workers} workers…")

    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in files:
            futures.append(
                pool.submit(
                    process_prompt,
                    f,
                    output_dir,
                    client,
                    args.model,
                    args.max_output_tokens,
                )
            )

        for fut in as_completed(futures):
            fut.result()

    print("\nAll prompts processed.")

if __name__ == "__main__":
    main()
