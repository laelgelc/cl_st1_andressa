# Python
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional

import pandas as pd


@dataclass(frozen=True)
class Ph1Paths:
    base: Path
    raw_dir: Path
    tables_dir: Path
    logs_dir: Path
    raw_posts: Path
    raw_comments: Path
    posts_parquet: Path
    comments_parquet: Path

    @staticmethod
    def create(base: Path) -> "Ph1Paths":
        raw = base / "raw"
        tables = base / "tables"
        logs = base / "logs"
        raw.mkdir(parents=True, exist_ok=True)
        tables.mkdir(parents=True, exist_ok=True)
        logs.mkdir(parents=True, exist_ok=True)
        return Ph1Paths(
            base=base,
            raw_dir=raw,
            tables_dir=tables,
            logs_dir=logs,
            raw_posts=raw / "reddit_submissions.ndjson",
            raw_comments=raw / "reddit_comments.ndjson",
            posts_parquet=tables / "posts.parquet",
            comments_parquet=tables / "comments.parquet",
        )


def append_ndjson(path: Path, rows: Iterable[Mapping]) -> int:
    count = 0
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_parquet(path: Path, rows: list[Mapping], columns: Optional[list[str]] = None) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows, columns=columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return len(df)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_provenance(path: Path, obj: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)