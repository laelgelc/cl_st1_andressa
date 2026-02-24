#!/usr/bin/env python3
from pathlib import Path


# -------------------------------------------
# CONFIG
# -------------------------------------------
DIR_BACKGROUND = Path("corpus/02_extracted")
DIR_SUMMARY    = Path("corpus/03_summary")
DIR_OUT        = Path("corpus/04_prompt_summary_guided")

DIR_OUT.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a member of a loneliness-related subreddit on Reddit where people write self-disclosure posts about loneliness.\n"
)

USER_PROMPT = (
    "Read the summary below.\n\n"
    "TASK:\n\n"
    "Your task is to write a post based ONLY on the summary provided below.\n"
    "- Do not acknowledge this prompt; respond straightaway.\n"
    "- Do not include a title line.\n"
    "- Write only the body of the post.\n"
    "- Write in English.\n"
    "- Do not invent information beyond what is in the summary.\n"
    "- Length: 120–500 words.\n"
)


# -------------------------------------------
# MAIN
# -------------------------------------------

def main():
    index_entries = []
    counter = 1

    for bg_file in sorted(DIR_BACKGROUND.glob("*_extracted.txt")):
        base = bg_file.stem.split("_")[0]

        # Load summary file
        summary_file = DIR_SUMMARY / f"{base}_extracted_summarized.txt"
        if not summary_file.exists():
            continue

        summary_text = summary_file.read_text(encoding="utf-8", errors="ignore")
        if not summary_text:
            continue

        # BUILD THE FULL PROMPT
        full_prompt = (
            f"SYSTEM PROMPT:\n{SYSTEM_PROMPT}\n"
            f"USER PROMPT:\n{USER_PROMPT}\n"
            f"{summary_text}\n"
        )

        # Save to tXXX.txt
        out_name = f"t{counter:03d}.txt"
        (DIR_OUT / out_name).write_text(full_prompt, encoding="utf-8")

        index_entries.append(f"{out_name} {base}")
        counter += 1

    Path("file_index.txt").write_text("\n".join(index_entries), encoding="utf-8")
    print(f"Done. Created {counter-1} prompts.")


if __name__ == "__main__":
    main()
