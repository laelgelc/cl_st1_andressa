#!/usr/bin/env python3
"""
summarise_posts_v2.py

Reads .txt posts structured in paragraphs and prompts GPT to summarise them.

Uses the OpenAI Python SDK (Responses API) to avoid max_tokens/max_completion_tokens
parameter mismatches across model families.

Usage:
    python summarise_posts_v2.py \
        --input corpus/02_extracted \
        --output corpus/03_summary \
        --model gpt-5.1 \
        --workers 4 \
        --test 10
"""

import argparse
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv


# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


# ------------------------------------------------------------
# API (OpenAI SDK)
# ------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Install with: conda install openai")
    sys.exit(1)


# ------------------------------------------------------------
# CLI ARGUMENTS
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize posts using GPT (OpenAI SDK / Responses API).")
    parser.add_argument("--input", "-i", required=True, help="Folder containing post .txt files.")
    parser.add_argument("--output", "-o", required=True, help="Folder to save GPT summaries.")
    parser.add_argument("--model", "-m", default="gpt-5.1", help="GPT model to use (default: gpt-5.1).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=3000, help="Maximum output tokens.")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers.")
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="If set, process only the first N .txt files in the input folder (e.g., --test 10).",
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
# PROMPTS
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
""".strip()


# ------------------------------------------------------------
# OPENAI CALL (Responses API)
# ------------------------------------------------------------
def gpt_api_call_v2(
        client: OpenAI,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
) -> str:
    """
    One request = one isolated context.

    We do NOT reuse any conversation/thread state. Each call provides only the
    system+user messages for that single document.
    """
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=max_output_tokens,
        temperature=0.0,
    )

    out = getattr(resp, "output_text", None)
    if not out:
        raise RuntimeError("API returned empty output.")
    return out


# ------------------------------------------------------------
# WORKER
# ------------------------------------------------------------
def process_file(
        file_path: Path,
        output_dir: Path,
        client: OpenAI,
        model: str,
        max_tokens: int,
) -> bool:
    try:
        print(f"[WORKER] Processing: {file_path.name}")

        file_text = read_text(file_path)
        if not file_text.strip():
            raise RuntimeError("Input file is empty.")

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(file_text)

        response = gpt_api_call_v2(
            client=client,
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
def main() -> int:
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No .txt files found in input folder.")
        return 0

    if args.test is not None:
        if args.test <= 0:
            print("Error: --test must be a positive integer.")
            return 1
        files = files[: args.test]
        print(f"[TEST MODE] Limiting to first {len(files)} files.\n")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        return 1

    client = OpenAI(api_key=api_key)

    print(f"Processing {len(files)} posts with {args.workers} workers...\n")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(process_file, f, output_dir, client, args.model, args.max_output_tokens)
            for f in files
        ]
        for fut in as_completed(futures):
            fut.result()

    print("\nCompleted summarizing posts using GPT (OpenAI SDK / Responses API).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())