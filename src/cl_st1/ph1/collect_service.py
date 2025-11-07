# Python
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

import pandas as pd
from praw.models import Submission, Comment

from cl_st1.common.storage import Ph1Paths, append_ndjson, write_parquet, now_utc_iso, write_provenance
from cl_st1.ph1.reddit_client import get_reddit

ProgressCb = Callable[[str], None]
CountsCb = Callable[[int, int], None]

POST_COLUMNS = [
    "id", "subreddit", "created_utc", "author", "title", "selftext", "score",
    "num_comments", "url", "permalink", "over_18", "removed_by_category"
]

COMMENT_COLUMNS = [
    "id", "link_id", "parent_id", "subreddit", "created_utc", "author", "body",
    "score", "permalink", "removed_by_category"
]


def sub_to_row(s: Submission) -> Dict[str, object]:
    return {
        "id": s.id,
        "subreddit": str(s.subreddit),
        "created_utc": int(getattr(s, "created_utc", 0)),
        "author": str(getattr(s.author, "name", None)) if s.author else None,
        "title": s.title,
        "selftext": s.selftext,
        "score": s.score,
        "num_comments": s.num_comments,
        "url": s.url,
        "permalink": f"https://reddit.com{s.permalink}",
        "over_18": bool(getattr(s, "over_18", False)),
        "removed_by_category": getattr(s, "removed_by_category", None),
    }


def comment_to_row(c: Comment) -> Dict[str, object]:
    return {
        "id": c.id,
        "link_id": c.link_id.replace("t3_", "") if getattr(c, "link_id", None) else None,
        "parent_id": c.parent_id,
        "subreddit": str(c.subreddit),
        "created_utc": int(getattr(c, "created_utc", 0)),
        "author": str(getattr(c.author, "name", None)) if c.author else None,
        "body": c.body,
        "score": c.score,
        "permalink": f"https://reddit.com{c.permalink}",
        "removed_by_category": getattr(c, "removed_by_category", None),
    }


def backoff_sleep(attempt: int) -> None:
    time.sleep(min(60, 2 ** attempt))


def fetch_submissions(sr_name: str, sort: str, limit: Optional[int], after_utc: Optional[int], before_utc: Optional[int],
                      progress: Optional[ProgressCb]) -> Iterable[Submission]:
    reddit = get_reddit()
    sr = reddit.subreddit(sr_name)
    if sort == "new":
        stream = sr.new(limit=limit)
    elif sort == "top":
        stream = sr.top(time_filter="all", limit=limit)
    else:
        stream = sr.new(limit=limit)

    for s in stream:
        ts = int(getattr(s, "created_utc", 0))
        if after_utc and ts < after_utc:
            continue
        if before_utc and ts > before_utc:
            continue
        if progress:
            progress(f"{sr_name}: fetched submission {s.id}")
        yield s


def fetch_comments_for_submission(sub: Submission, limit: Optional[int], progress: Optional[ProgressCb]) -> Iterable[Comment]:
    sub.comments.replace_more(limit=0)
    comments = sub.comments.list()
    count = 0
    for c in comments:
        if limit is not None and count >= limit:
            break
        if progress:
            progress(f"{sub.subreddit}: fetched comment {c.id} on {sub.id}")
        count += 1
        yield c


def collect(
        subreddits: list[str],
        out_dir: str = "data/ph1",
        sort: str = "new",
        per_subreddit_limit: Optional[int] = 1000,
        include_comments: bool = True,
        comments_limit_per_post: int = 300,
        after_utc: Optional[int] = None,
        before_utc: Optional[int] = None,
        progress: Optional[ProgressCb] = None,
        counts: Optional[CountsCb] = None,
) -> Dict[str, int]:
    """
    Main orchestration used by GUI/CLI.
    """
    paths = Ph1Paths.create(Path(out_dir))
    posts_rows: List[Dict[str, object]] = []
    comments_rows: List[Dict[str, object]] = []
    posts_total = 0
    comments_total = 0
    attempt = 0

    start_iso = now_utc_iso()

    for sr in subreddits:
        while True:
            try:
                for s in fetch_submissions(sr, sort, per_subreddit_limit, after_utc, before_utc, progress):
                    row = sub_to_row(s)
                    append_ndjson(paths.raw_posts, [row])
                    posts_rows.append(row)
                    posts_total += 1
                    if include_comments:
                        for c in fetch_comments_for_submission(s, comments_limit_per_post, progress):
                            crow = comment_to_row(c)
                            append_ndjson(paths.raw_comments, [crow])
                            comments_rows.append(crow)
                            comments_total += 1
                    if counts:
                        counts(posts_total, comments_total)
                break
            except Exception as e:
                attempt += 1
                if progress:
                    progress(f"[{sr}] Error: {e}; retrying attempt {attempt}")
                backoff_sleep(attempt)
        attempt = 0

    # Write parquet tables
    write_parquet(paths.posts_parquet, posts_rows, POST_COLUMNS)
    if include_comments:
        write_parquet(paths.comments_parquet, comments_rows, COMMENT_COLUMNS)

    # Provenance
    prov = {
        "started_at": start_iso,
        "finished_at": now_utc_iso(),
        "params": {
            "subreddits": subreddits,
            "sort": sort,
            "per_subreddit_limit": per_subreddit_limit,
            "include_comments": include_comments,
            "comments_limit_per_post": comments_limit_per_post,
            "after_utc": after_utc,
            "before_utc": before_utc,
            "out_dir": out_dir,
        },
        "counts": {"posts": posts_total, "comments": comments_total},
        "versions": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "praw": __import__("praw").__version__,
            "pandas": pd.__version__,
            "pyarrow": __import__("pyarrow").__version__,
        },
    }
    write_provenance(Path(out_dir) / "logs" / f"ph1_run_{int(datetime.now(timezone.utc).timestamp())}.json", prov)

    if progress:
        progress("Collection finished.")
    return {"posts": posts_total, "comments": comments_total}