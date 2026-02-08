# Python
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cl_st1.ph1.cli import ph1_cli


def _ts(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> int:
    return int(datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc).timestamp())


def test_resolve_time_window_year_inclusive_end_of_year():
    tw = ph1_cli._resolve_time_window(
        year=2024,
        after_utc=None,
        before_utc=None,
        after_date=None,
        before_date=None,
    )
    assert tw.after_utc == _ts(2024, 1, 1, 0, 0, 0)
    assert tw.before_utc == _ts(2025, 1, 1, 0, 0, 0) - 1


def test_resolve_time_window_after_date_only():
    tw = ph1_cli._resolve_time_window(
        year=None,
        after_utc=None,
        before_utc=None,
        after_date="2024-01-01",
        before_date=None,
    )
    assert tw.after_utc == _ts(2024, 1, 1, 0, 0, 0)
    assert tw.before_utc is None


def test_resolve_time_window_after_and_before_date_are_inclusive_end_date():
    tw = ph1_cli._resolve_time_window(
        year=None,
        after_utc=None,
        before_utc=None,
        after_date="2024-01-01",
        before_date="2024-01-07",
    )
    assert tw.after_utc == _ts(2024, 1, 1, 0, 0, 0)
    # before_date is treated as inclusive end-of-day: start_of_next_day - 1
    assert tw.before_utc == _ts(2024, 1, 8, 0, 0, 0) - 1


def test_resolve_time_window_rejects_year_combined_with_other_time_args():
    with pytest.raises(SystemExit):
        ph1_cli._resolve_time_window(
            year=2024,
            after_utc=_ts(2024, 1, 1),
            before_utc=None,
            after_date=None,
            before_date=None,
        )


def test_resolve_time_window_requires_after_when_no_year():
    with pytest.raises(SystemExit):
        ph1_cli._resolve_time_window(
            year=None,
            after_utc=None,
            before_utc=None,
            after_date=None,
            before_date=None,
        )


def test_resolve_time_window_rejects_before_lt_after():
    with pytest.raises(SystemExit):
        ph1_cli._resolve_time_window(
            year=None,
            after_utc=_ts(2024, 1, 2),
            before_utc=_ts(2024, 1, 1),
            after_date=None,
            before_date=None,
        )