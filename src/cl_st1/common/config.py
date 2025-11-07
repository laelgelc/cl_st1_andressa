# Python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    reddit_client_id: str
    reddit_client_secret: str
    user_agent: str
    out_dir: Path = Path("data/ph1")


def get_settings(env_file: Optional[Path] = Path("env/.env")) -> Settings:
    """
    Load credentials and basic settings from env/.env and environment variables.

    Required:
      - REDDIT_CLIENT_ID
      - REDDIT_CLIENT_SECRET
    Optional:
      - USER_AGENT (defaults to 'cl_st1_loneliness/1.0 (by u/unknown)')
    """
    if env_file and env_file.exists():
        load_dotenv(dotenv_path=env_file)

    client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
    user_agent = os.getenv(
        "USER_AGENT",
        "cl_st1_loneliness/1.0 (by u/unknown)",
    ).strip()

    missing = []
    if not client_id:
        missing.append("REDDIT_CLIENT_ID")
    if not client_secret:
        missing.append("REDDIT_CLIENT_SECRET")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in env/.env (see .env.template) or your shell environment."
        )

    return Settings(
        reddit_client_id=client_id,
        reddit_client_secret=client_secret,
        user_agent=user_agent,
    )