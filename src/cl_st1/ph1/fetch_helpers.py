# Python
from __future__ import annotations

from typing import Dict
from praw.models import Submission, Comment


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