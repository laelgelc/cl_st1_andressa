# Python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from cl_st1.ph1.collect_service import collect


def _utc_epoch(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _parse_yyyy_mm_dd(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _utc_ymd_from_epoch(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _make_safe_subdir(name: str) -> str:
    # Keep it filesystem-friendly and stable.
    cleaned = []
    for ch in name.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_") or "run"


def _subreddits_label(subreddits: list[str], max_len: int = 64) -> str:
    # Stable + readable label, but capped to avoid ridiculously long folder names.
    joined = "+".join(subreddits)
    safe = _make_safe_subdir(joined)
    if len(safe) <= max_len:
        return safe
    return safe[: max_len - len("_etc")] + "_etc"


def _default_run_subdir(
        *,
        year: Optional[int],
        after_utc: int,
        before_utc: Optional[int],
        after_date: Optional[str],
        before_date: Optional[str],
        subreddits: list[str],
) -> str:
    sr = _subreddits_label(subreddits)

    if year is not None:
        return _make_safe_subdir(f"{year}_{sr}")

    # Prefer the user's explicit date inputs (more readable), otherwise derive from epoch.
    start = after_date if after_date else _utc_ymd_from_epoch(after_utc)
    end = before_date if before_date else (_utc_ymd_from_epoch(before_utc) if before_utc is not None else "open")

    return _make_safe_subdir(f"window_{start}_to_{end}_{sr}")


@dataclass(frozen=True)
class TimeWindow:
    after_utc: int
    before_utc: Optional[int]


def _resolve_time_window(
        *,
        year: Optional[int],
        after_utc: Optional[int],
        before_utc: Optional[int],
        after_date: Optional[str],
        before_date: Optional[str],
) -> TimeWindow:
    # Either use --year OR use an explicit time window.
    if year is not None:
        if any(v is not None for v in (after_utc, before_utc, after_date, before_date)):
            raise SystemExit(
                "Error: --year cannot be combined with --after-utc/--before-utc/--after-date/--before-date"
            )

        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        next_year = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        # Inclusive end-of-year (collect_service skips ts > before_utc)
        return TimeWindow(after_utc=_utc_epoch(start), before_utc=_utc_epoch(next_year) - 1)

    if after_utc is None and after_date is None:
        raise SystemExit("Error: provide either --year OR --after-utc OR --after-date")

    if after_utc is not None and after_date is not None:
        raise SystemExit("Error: use only one of --after-utc or --after-date")

    if before_utc is not None and before_date is not None:
        raise SystemExit("Error: use only one of --before-utc or --before-date")

    resolved_after = after_utc if after_utc is not None else _utc_epoch(_parse_yyyy_mm_dd(after_date))  # type: ignore[arg-type]
    resolved_before = (
        before_utc
        if before_utc is not None
        else (
            _utc_epoch(_parse_yyyy_mm_dd(before_date) + timedelta(days=1)) - 1
            if before_date
            else None
        )
    )

    if resolved_before is not None and resolved_before < resolved_after:
        raise SystemExit("Error: before must be >= after")

    return TimeWindow(after_utc=resolved_after, before_utc=resolved_before)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Phase 1 — Reddit Data Collection")
    p.add_argument("-s", "--subreddits", required=True, help="Comma-separated list of subreddits")
    p.add_argument("--sort", default="new", choices=["new", "top"])
    p.add_argument("--per-subreddit-limit", type=int, default=1000)

    # Study focuses on posts: default to NOT collecting comments, but allow enabling.
    p.add_argument("--include-comments", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--comments-limit-per-post", type=int, default=300)

    # Time window options: either --year OR explicit after/before (utc seconds or dates).
    p.add_argument("--year", type=int, help="Collect within a calendar year in UTC (e.g., 2024).")
    p.add_argument("--after-utc", type=int, help="Epoch seconds (UTC). Required unless --year/--after-date is used.")
    p.add_argument("--before-utc", type=int, help="Epoch seconds (UTC). Optional.")
    p.add_argument("--after-date", help="UTC date (YYYY-MM-DD). Alternative to --after-utc.")
    p.add_argument("--before-date", help="UTC date (YYYY-MM-DD). Alternative to --before-utc.")

    # Output directory behavior:
    # - If --out-dir is omitted:
    #   - with --year: defaults to data/ph1/<year>_<subreddits>
    #   - with a custom window: defaults to data/ph1/window_<start>_to_<end|open>_<subreddits>
    # - --run-subdir lets you set a custom run folder under --out-dir-base.
    p.add_argument("--out-dir", default=None, help="Explicit output directory. If set, overrides auto folder naming.")
    p.add_argument("--out-dir-base", default="data/ph1", help="Base output directory for auto-named runs.")
    p.add_argument("--run-subdir", default=None, help="Optional subfolder name under --out-dir-base (e.g., 'pilot_2024q1').")

    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    subs = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    if not subs:
        raise SystemExit("Error: --subreddits must include at least one subreddit name")

    tw = _resolve_time_window(
        year=args.year,
        after_utc=args.after_utc,
        before_utc=args.before_utc,
        after_date=args.after_date,
        before_date=args.before_date,
    )

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
                    year=args.year,
                    after_utc=tw.after_utc,
                    before_utc=tw.before_utc,
                    after_date=args.after_date,
                    before_date=args.before_date,
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
        sort=args.sort,
        per_subreddit_limit=args.per_subreddit_limit,
        include_comments=args.include_comments,
        comments_limit_per_post=args.comments_limit_per_post,
        after_utc=tw.after_utc,
        before_utc=tw.before_utc,
        progress=progress,
        counts=counts,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())