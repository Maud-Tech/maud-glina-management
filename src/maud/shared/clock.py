"""Relógio injetável. Código de negócio nunca chama datetime.now(): pede `get_clock().now()`.

Em teste, `use_clock(FixedClock(...))` congela o tempo (expiração de reserva, D-1, etc.).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass
class FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current = self.current + delta


_clock: Clock = SystemClock()


def get_clock() -> Clock:
    return _clock


@contextmanager
def use_clock(clock: Clock) -> Iterator[Clock]:
    global _clock
    previous = _clock
    _clock = clock
    try:
        yield clock
    finally:
        _clock = previous
