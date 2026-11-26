from datetime import UTC, datetime, timedelta

import pytest

from maud.jobs.scheduler import Job, Scheduler
from maud.shared.clock import FixedClock

T0 = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


def test_runs_at_startup_then_only_on_interval() -> None:
    calls: list[str] = []
    clock = FixedClock(T0)
    scheduler = Scheduler([Job("a", timedelta(minutes=1), lambda: calls.append("a"))], clock)

    assert scheduler.run_due() == ["a"]
    clock.advance(timedelta(seconds=59))
    assert scheduler.run_due() == []
    clock.advance(timedelta(seconds=1))
    assert scheduler.run_due() == ["a"]
    assert calls == ["a", "a"]


def test_failing_job_does_not_stop_the_others() -> None:
    calls: list[str] = []

    def boom() -> None:
        raise RuntimeError("falhou")

    scheduler = Scheduler(
        [
            Job("boom", timedelta(minutes=1), boom),
            Job("ok", timedelta(minutes=1), lambda: calls.append("ok")),
        ],
        FixedClock(T0),
    )
    assert scheduler.run_due() == ["boom", "ok"]
    assert calls == ["ok"]


def test_duplicate_name_is_rejected() -> None:
    job = Job("a", timedelta(minutes=1), lambda: None)
    with pytest.raises(ValueError):
        Scheduler([job, job], FixedClock(T0))
