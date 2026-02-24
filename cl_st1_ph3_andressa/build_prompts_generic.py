#!/usr/bin/env python3
from pathlib import Path
import json


# -------------------------------------------
# CONFIG
# -------------------------------------------
DIR_BACKGROUND = Path("corpus/02_extracted")
DIR_OUT        = Path("corpus/04_prompt_generic")

DIR_OUT.mkdir(parents=True, exist_ok=True)

# NDJSON source for original post lengths (post_id -> selftext_word_count)
POSTS_NDJSON = (Path(__file__).resolve().parent / ".." / "data" / "ph2" / "human_reddit_posts_2_no_outliers.ndjson").resolve()

SYSTEM_PROMPT = (
    "You are a member of a loneliness-related subreddit on Reddit where people write self-disclosure posts about loneliness.\n"
)

USER_PROMPT = (
    "\n"
    "TASK:\n\n"
    "Your task is to write a self-disclosure post about loneliness.\n"
    "- Do not acknowledge this prompt; respond straightaway.\n"
    "- Do not include a title line.\n"
    "- Write only the body of the post.\n"
    "- Write in English.\n"
)


# -------------------------------------------
# HELPERS
# -------------------------------------------

def load_post_word_counts(ndjson_path: Path) -> dict[str, int]:
    """
    Load post_id -> selftext_word_count mapping from an NDJSON file.
    """
    if not ndjson_path.exists():
        raise FileNotFoundError(f"NDJSON not found: {ndjson_path}")

    mapping: dict[str, int] = {}
    with ndjson_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON on line {line_no} in {ndjson_path}: {e}") from e

            post_id = obj.get("post_id")
            wc = obj.get("selftext_word_count")
            if isinstance(post_id, str) and isinstance(wc, int):
                mapping[post_id] = wc

    return mapping


def length_line_from_word_count(word_count: int) -> str:
    """
    Convert an original post word count into an instruction line.
    Uses a +/-20% band (rounded) with a small minimum.
    """
    wc = max(1, int(word_count))
    lower = max(10, int(round(wc * 0.8)))
    upper = max(lower + 10, int(round(wc * 1.2)))
    return f"- Length: {lower}–{upper} words.\n"


# -------------------------------------------
# MAIN
# -------------------------------------------

def main():
    post_word_counts = load_post_word_counts(POSTS_NDJSON)

    index_entries = []
    counter = 1

    for bg_file in sorted(DIR_BACKGROUND.glob("*_extracted.txt")):
        base = bg_file.stem.split("_")[0]

        # Look up original post length via post_id == base
        wc = post_word_counts.get(base)
        if wc is None:
            # If you prefer strict behavior, replace this with: `continue` or `raise`.
            print(f"[WARN] No word count found for post_id={base!r} in {POSTS_NDJSON.name}; using default length.")
            length_line = "- Length: 120–500 words.\n"
        else:
            length_line = length_line_from_word_count(wc)

        constraints_block = (
            "Constraints (must follow):\n"
            "- Avoid generic motivational or uplifting endings.\n"
        )

        # BUILD THE FULL PROMPT (no summaries used)
        full_prompt = (
            f"SYSTEM PROMPT:\n{SYSTEM_PROMPT}\n"
            f"USER PROMPT:\n{USER_PROMPT}"
            f"{length_line}\n"
            f"{constraints_block}\n"
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