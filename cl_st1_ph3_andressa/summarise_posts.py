#!/usr/bin/env python3
"""
summarise_blog_posts.py

Reads .txt blog posts structured in paragraphs and prompts Grok to summarise them.

Usage:
    python summarise_blog_posts.py \
        --input input_folder \
        --output output_folder \
        --model grok-4 \
        --workers 4
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
        description="Summarize blog posts using Grok."
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Folder containing blog post .txt files.")
    parser.add_argument("--output", "-o", required=True,
                        help="Folder to save Grok summaries.")
    parser.add_argument("--model", "-m", default="grok-4",
                        help="Grok model to use (default: grok-4).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=3000,
                        help="Maximum output tokens.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel workers.")
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
        "You are an expert analyst who reads Greenpeace website blog posts. "
        "You must NOT invent information under any circumstances. "
        "You must summarize each blog post into a concise description "
        "of what was discussed."
    )

def build_user_prompt(file_text: str) -> str:
    return f"""
Read the blog post below.

TASK:

Write a summary in running prose of the main ideas:
- Write the summary concisely. Your summary should have no more than 100 words.
- DO NOT invent information.
- DO NOT include analysis unrelated to the text.
- Only summarise what was actually said.

--------------------------------
TEXT BELOW
--------------------------------
{file_text}
"""


# ------------------------------------------------------------
# GROK API CALL
# ------------------------------------------------------------

def grok_api_call(model: str, system_prompt: str, user_prompt: str,
                  max_output_tokens: int) -> str:

    if "XAI_API_KEY" not in os.environ:
        raise RuntimeError("Environment variable XAI_API_KEY not set.")

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_output_tokens,
        "temperature": 0.0
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))

    if resp.status_code != 200:
        raise RuntimeError(f"Grok API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


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

        response = grok_api_call(
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

    print(f"Processing {len(files)} blog posts with {args.workers} workers...\n")

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

    print("\nCompleted summarizing blog posts using Grok.")


if __name__ == "__main__":
    main()
