import signal
from types import FrameType
from typing import Any

from django.core.management.base import BaseCommand

from maud.jobs.schedule import JOBS
from maud.jobs.scheduler import run_forever
from maud.shared.clock import get_clock


class Command(BaseCommand):
    help = "Roda o Worker: expira reservas, despacha eventos, concilia (ver maud/jobs/schedule.py)."

    def handle(self, *args: Any, **options: Any) -> None:
        stop = False

        def _request_stop(signum: int, frame: FrameType | None) -> None:
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, _request_stop)
        signal.signal(signal.SIGTERM, _request_stop)
        run_forever(JOBS, get_clock(), should_stop=lambda: stop)
