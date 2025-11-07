# Python
from __future__ import annotations

import argparse

from cl_st1.ph1.collect_service import collect


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Phase 1 — Reddit Data Collection")
    p.add_argument("-s", "--subreddits", required=True, help="Comma-separated list of subreddits")
    p.add_argument("--sort", default="new", choices=["new", "top"])
    p.add_argument("--per-subreddit-limit", type=int, default=1000)
    p.add_argument("--include-comments", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--comments-limit-per-post", type=int, default=300)
    p.add_argument("--after-utc", type=int, required=True)
    p.add_argument("--before-utc", type=int)
    p.add_argument("--out-dir", default="data/ph1")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    subs = [s.strip() for s in args.subreddits.split(",") if s.strip()]

    def progress(msg: str):
        print(msg)

    def counts(posts: int, comments: int):
        print(f"Counts — posts: {posts}, comments: {comments}")

    collect(
        subreddits=subs,
        out_dir=args.out_dir,
        sort=args.sort,
        per_subreddit_limit=args.per_subreddit_limit,
        include_comments=args.include_comments,
        comments_limit_per_post=args.comments_limit_per_post,
        after_utc=args.after_utc,
        before_utc=args.before_utc,
        progress=progress,
        counts=counts,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())