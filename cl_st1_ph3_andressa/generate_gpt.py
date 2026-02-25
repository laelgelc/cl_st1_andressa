#!/usr/bin/env python3
"""
generate_gpt.py

Reads prompt files (t001.txt, t002.txt, ...) from an input directory,
extracts system and user prompts from the file text,
submits them to GPT,
and saves the model output to corpus/05_persona_gpt with the SAME filename.

Parallel workers included.

Usage:
    python generate_gpt.py \
        --input corpus/04_prompt \
        --output corpus/05_gpt \
        --model gpt-5.1 \
        --workers 4
"""

import argparse
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


# ---------------------------------------------
# API
# ---------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: Install with: conda install openai")
    sys.exit(1)

# ---------------------------------------------
# CLI
# ---------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send oral-history persona prompts to GPT."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing tXXX prompt files (e.g., corpus/04_prompt)."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory (e.g., corpus/05_persona_gpt)."
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-5.1",
        help="OpenAI model to use (default: gpt-5.1)."
    )
    parser.add_argument(
        "--max-output-tokens", "-t",
        type=int,
        default=6000,
        help="Maximum output tokens."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers."
    )
    return parser.parse_args()

# ---------------------------------------------
# Helpers
# ---------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_system_and_user(full_text: str):
    """
    Extract:

    SYSTEM PROMPT:
    <system text>

    USER PROMPT:
    <user text>
    (everything after "USER PROMPT:" up to end of file)
    """

    # Extract system prompt
    sys_match = re.search(
        r"SYSTEM PROMPT:\s*(.+?)\nUSER PROMPT:",
        full_text,
        re.DOTALL
    )
    if not sys_match:
        raise ValueError("Could not locate SYSTEM PROMPT block.")

    system_prompt = sys_match.group(1).strip()

    # Extract user prompt (from USER PROMPT to end)
    user_match = re.search(
        r"USER PROMPT:\s*(.+)",
        full_text,
        re.DOTALL
    )
    if not user_match:
        raise ValueError("Could not locate USER PROMPT block.")

    user_prompt = user_match.group(1).strip()

    return system_prompt, user_prompt


def call_api(client: OpenAI, model: str, system_prompt: str,
             user_prompt: str, max_output_tokens: int) -> str:

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=max_output_tokens,
        temperature=0.7,
    )

    out = response.output_text
    if not out:
        raise RuntimeError("API returned empty output.")
    return out


# ---------------------------------------------
# Worker
# ---------------------------------------------
def process_prompt(
    path: Path,
    output_dir: Path,
    client: OpenAI,
    model: str,
    max_tokens: int,
):

    try:
        print(f"[WORKER] Reading prompt: {path.name}")
        full_text = read_text(path)

        system_prompt, user_prompt = extract_system_and_user(full_text)

        print(f"[WORKER] Calling API for {path.name} …")
        result = call_api(
            client=client,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        # -------------------------------
        # NEW: Write as t001_gpt.txt
        # -------------------------------
        stem = path.stem                       # "t001"
        outname = f"{stem}_gpt.txt"            # "t001_gpt.txt"
        outpath = output_dir / outname

        write_text(outpath, result)
        print(f"[WORKER] Saved → {outpath}")

        return True

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False

# ---------------------------------------------
# Main
# ---------------------------------------------
def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("t*.txt"))
    if not files:
        print("No prompt files found.")
        sys.exit(0)

    # API client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    print(f"Processing {len(files)} prompts with {args.workers} workers…\n")

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

    print("\nAll prompts processed successfully with GPT.")


if __name__ == "__main__":
    main()
