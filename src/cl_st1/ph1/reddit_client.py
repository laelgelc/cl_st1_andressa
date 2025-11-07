# Python
from __future__ import annotations

import praw

from cl_st1.common.config import get_settings


def get_reddit() -> praw.Reddit:
    """
    Construct an authenticated PRAW client using credentials from env/.env.

    Required env vars (see env/.env.template):
      - REDDIT_CLIENT_ID
      - REDDIT_CLIENT_SECRET
    Optional:
      - USER_AGENT
    """
    s = get_settings()
    return praw.Reddit(
        client_id=s.reddit_client_id,
        client_secret=s.reddit_client_secret,
        user_agent=s.user_agent,
        ratelimit_seconds=5,
    )