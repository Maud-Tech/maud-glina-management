"""O QUE roda QUANDO. O código de cada job mora no módulo dono, exposto pelo jobs.py dele."""

from datetime import timedelta

from maud.integration import jobs as integration_jobs
from maud.jobs.scheduler import Job

JOBS: list[Job] = [
    Job("integration.dispatch_outbox", timedelta(seconds=10), integration_jobs.dispatch_outbox),
]
