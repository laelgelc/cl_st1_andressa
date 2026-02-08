# Python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


from cl_st1.ph1.collect_service import collect


def _make_safe_subdir(name: str) -> str:
    cleaned = []
    for ch in name.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or "run"


def _subreddits_label(subreddits: list[str], max_len: int = 64) -> str:
    joined = "+".join(subreddits)
    safe = _make_safe_subdir(joined)
    if len(safe) <= max_len:
        return safe
    return safe[: max_len - len("_etc")] + "_etc"


def _default_run_subdir(*, listing: str, limit: int | None, subreddits: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sr = _subreddits_label(subreddits)
    lim = "nolimit" if limit is None else str(int(limit))
    return _make_safe_subdir(f"{listing}_{lim}_{sr}_{ts}")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Phase 1 — Reddit Data Collection (listing + limit)")

    p.add_argument("-s", "--subreddits", required=True, help="Comma-separated list of subreddits")
    p.add_argument("--listing", default="new", choices=["new", "top"], help="Subreddit listing to fetch from")
    p.add_argument(
        "--per-subreddit-limit",
        type=int,
        default=1000,
        help="Maximum number of posts to request from the listing per subreddit",
    )

    # Study focuses on posts: default to NOT collecting comments, but allow enabling.
    p.add_argument("--include-comments", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--comments-limit-per-post", type=int, default=300)

    # Output directory behavior:
    # - If --out-dir is provided, use it directly.
    # - Otherwise, use --out-dir-base and create an auto-named run subfolder.
    # - --run-subdir overrides the auto name under --out-dir-base.
    p.add_argument("--out-dir", default=None, help="Explicit output directory. If set, overrides auto naming.")
    p.add_argument("--out-dir-base", default="data/ph1", help="Base output directory for auto-named runs.")
    p.add_argument("--run-subdir", default=None, help="Optional subfolder name under --out-dir-base.")

    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    subs = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    if not subs:
        raise SystemExit("Error: --subreddits must include at least one subreddit name")

    if args.per_subreddit_limit is not None and args.per_subreddit_limit <= 0:
        raise SystemExit("Error: --per-subreddit-limit must be a positive integer")

    if args.out_dir is not None:
        out_dir = args.out_dir
    else:
        base = Path(args.out_dir_base)
        if args.run_subdir:
            out_dir = str(base / args.run_subdir)
        else:
            out_dir = str(
                base
                / _default_run_subdir(
                    listing=args.listing,
                    limit=args.per_subreddit_limit,
                    subreddits=subs,
                )
            )

    def progress(msg: str):
        print(msg)

    def counts(posts: int, comments: int):
        print(f"Counts — posts: {posts}, comments: {comments}")

    collect(
        subreddits=subs,
        out_dir=out_dir,
        listing=args.listing,
        per_subreddit_limit=args.per_subreddit_limit,
        include_comments=args.include_comments,
        comments_limit_per_post=args.comments_limit_per_post,
        progress=progress,
        counts=counts,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())