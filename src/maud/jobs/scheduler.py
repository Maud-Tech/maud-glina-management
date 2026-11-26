"""Agendador do Worker. Simples de propósito: sem Redis/Celery (ver docs/adr/0004).

- Uma instância só: `pg_try_advisory_lock`; a segunda instância sai com erro.
- Cada job roda isolado: exceção num job é logada e não derruba os outros.
- Cada job abre a própria transação (é responsabilidade do job, não do agendador).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import close_old_connections, connection

from maud.shared.clock import Clock

log = logging.getLogger(__name__)

WORKER_LOCK_KEY = 7_391_002  # chave fixa do advisory lock do Worker


class WorkerAlreadyRunningError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Job:
    name: str
    every: timedelta
    run: Callable[[], object]


class Scheduler:
    def __init__(self, jobs: Sequence[Job], clock: Clock) -> None:
        names = [job.name for job in jobs]
        if len(names) != len(set(names)):
            raise ValueError(f"jobs com nome repetido: {names}")
        self._jobs = list(jobs)
        self._clock = clock
        start = clock.now()
        self._next_run: dict[str, datetime] = {job.name: start for job in jobs}

    def run_due(self) -> list[str]:
        """Roda os jobs vencidos. Devolve os nomes que rodaram (com ou sem erro)."""
        ran: list[str] = []
        for job in self._jobs:
            now = self._clock.now()
            if now < self._next_run[job.name]:
                continue
            try:
                job.run()
            except Exception:
                log.exception("job %s falhou", job.name)
            self._next_run[job.name] = now + job.every
            ran.append(job.name)
        return ran


def run_forever(
    jobs: Sequence[Job],
    clock: Clock,
    *,
    should_stop: Callable[[], bool] = lambda: False,
    sleep: Callable[[int], None] = time.sleep,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [WORKER_LOCK_KEY])
        acquired = cursor.fetchone()
    if not acquired or not acquired[0]:
        raise WorkerAlreadyRunningError("outro Worker já está rodando (advisory lock ocupado)")

    scheduler = Scheduler(jobs, clock)
    log.info("worker iniciado com %d job(s): %s", len(jobs), [j.name for j in jobs])
    try:
        while not should_stop():
            close_old_connections()
            scheduler.run_due()
            sleep(1)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [WORKER_LOCK_KEY])
        log.info("worker parado")
