#!/usr/bin/env python3
"""
summarise_posts.py

Reads .txt posts structured in paragraphs and prompts GPT to summarise them.

Usage:
    python summarise_posts.py \
        --input input_folder \
        --output output_folder \
        --model gpt-5.1 \
        --workers 4 \
        --test 10
"""

import argparse
import os
import sys
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


# ------------------------------------------------------------
# CLI ARGUMENTS
# ------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize posts using GPT (OpenAI)."
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Folder containing post .txt files.")
    parser.add_argument("--output", "-o", required=True,
                        help="Folder to save GPT summaries.")
    parser.add_argument("--model", "-m", default="gpt-5.1",
                        help="GPT model to use (default: gpt-5.1).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=3000,
                        help="Maximum output tokens.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel workers.")
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="If set, process only the first N .txt files in the input folder (e.g., --test 10)."
    )
    return parser.parse_args()


# ------------------------------------------------------------
# I/O
# ------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ------------------------------------------------------------
# PROMPT CONSTRUCTION
# ------------------------------------------------------------

def build_system_prompt() -> str:
    return (
        "You are a member of a loneliness-related subreddit on Reddit where "
        "people write self-disclosure posts about loneliness."
    )

def build_user_prompt(file_text: str) -> str:
    return f"""
Read the post below.

TASK:

Your task is to write a short summary using ONLY the information in the post.
- Do not acknowledge this prompt; respond straightaway.
- Write in English.
- Do not invent information - just summarize the post.

--------------------------------
TEXT BELOW
--------------------------------
{file_text}
"""


# ------------------------------------------------------------
# OPENAI GPT API CALL
# ------------------------------------------------------------

def gpt_api_call(model: str, system_prompt: str, user_prompt: str,
                 max_output_tokens: int) -> str:
    """
    Calls OpenAI Chat Completions API using requests (no extra SDK dependency).

    Requires env var:
      - OPENAI_API_KEY
    """
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("Environment variable OPENAI_API_KEY not set.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
    }

    # Some newer OpenAI models (e.g., gpt-5.x) require `max_completion_tokens`
    # and reject `max_tokens`.
    if model.lower().startswith("gpt-5"):
        payload["max_completion_tokens"] = max_output_tokens
    else:
        payload["max_tokens"] = max_output_tokens

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as e:
        raise RuntimeError(f"OpenAI API request failed: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected OpenAI response shape: {data}") from e


# ------------------------------------------------------------
# WORKER
# ------------------------------------------------------------

def process_file(file_path: Path, output_dir: Path,
                 model: str, max_tokens: int):

    try:
        print(f"[WORKER] Processing: {file_path.name}")

        file_text = read_text(file_path)
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(file_text)

        response = gpt_api_call(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        outname = f"{file_path.stem}_summarized.txt"
        write_text(output_dir / outname, response)

        print(f"[WORKER] Saved → {outname}")
        return True

    except Exception as e:
        print(f"[ERROR] {file_path.name}: {e}")
        return False


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No .txt files found in input folder.")
        sys.exit(0)

    if args.test is not None:
        if args.test <= 0:
            print("Error: --test must be a positive integer.")
            sys.exit(1)
        files = files[:args.test]
        print(f"[TEST MODE] Limiting to first {len(files)} files.\n")

    print(f"Processing {len(files)} posts with {args.workers} workers...\n")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                process_file,
                f,
                output_dir,
                args.model,
                args.max_output_tokens,
            )
            for f in files
        ]
        for fut in as_completed(futures):
            fut.result()

    print("\nCompleted summarizing posts using GPT (OpenAI).")


if __name__ == "__main__":
    main()