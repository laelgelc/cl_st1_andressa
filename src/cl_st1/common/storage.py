from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Ph1Paths:
    base: Path
    raw_dir: Path
    logs_dir: Path
    raw_posts: Path
    raw_comments: Path

    @staticmethod
    def create(base: Path) -> "Ph1Paths":
        raw = base / "raw"
        logs = base / "logs"
        raw.mkdir(parents=True, exist_ok=True)
        logs.mkdir(parents=True, exist_ok=True)
        return Ph1Paths(
            base=base,
            raw_dir=raw,
            logs_dir=logs,
            raw_posts=raw / "reddit_submissions.ndjson",
            raw_comments=raw / "reddit_comments.ndjson",
        )


def append_ndjson(path: Path, rows: Iterable[Mapping]) -> int:
    count = 0
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += 1
    return count


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_provenance(path: Path, obj: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)