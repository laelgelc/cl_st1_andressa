from __future__ import annotations

from datetime import datetime, timezone


def make_safe_subdir(name: str) -> str:
    cleaned = []
    for ch in name.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or "run"


def subreddits_label(subreddits: list[str], max_len: int = 64) -> str:
    joined = "+".join(subreddits)
    safe = make_safe_subdir(joined)
    if len(safe) <= max_len:
        return safe
    return safe[: max_len - len("_etc")] + "_etc"


def default_run_subdir(*, listing: str, limit: int | None, subreddits: list[str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sr = subreddits_label(subreddits)
    lim = "nolimit" if limit is None else str(int(limit))
    return make_safe_subdir(f"{listing}_{lim}_{sr}_{ts}")
