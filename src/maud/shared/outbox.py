"""Transactional outbox: eventos para fora gravados junto com o fato, entregues pelo Worker.

- `publish` só funciona dentro de `transaction.atomic`: se o fato não comitar, o evento não existe.
- O despachante (módulo integration) usa `claim_batch` + `mark_sent`/`mark_failed`.
- Nome de evento: "<modulo>.<fato_no_passado>", ex.: "orders.reservation_held".
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from django.db import transaction

from maud.shared.clock import get_clock
from maud.shared.models import OutboxEvent

MAX_ATTEMPTS = 12
_BASE_BACKOFF = timedelta(seconds=30)
_MAX_BACKOFF = timedelta(hours=1)


def publish(
    event_type: str, *, aggregate_type: str, aggregate_id: str, payload: dict[str, Any]
) -> OutboxEvent:
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("outbox.publish() precisa rodar dentro de transaction.atomic()")
    now = get_clock().now()
    return OutboxEvent.objects.create(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        occurred_at=now,
        next_attempt_at=now,
    )


def claim_batch(limit: int = 50) -> list[OutboxEvent]:
    """Trava eventos vencidos (SKIP LOCKED). Chame dentro de transaction.atomic()."""
    now = get_clock().now()
    return list(
        OutboxEvent.objects.select_for_update(skip_locked=True)
        .filter(status=OutboxEvent.Status.PENDING, next_attempt_at__lte=now)
        .order_by("occurred_at")[:limit]
    )


def backoff_for(attempts: int) -> timedelta:
    delay: timedelta = _BASE_BACKOFF * (2 ** max(attempts - 1, 0))
    return min(delay, _MAX_BACKOFF)


def mark_sent(event: OutboxEvent) -> None:
    event.status = OutboxEvent.Status.SENT
    event.sent_at = get_clock().now()
    event.save(update_fields=["status", "sent_at"])


def mark_failed(event: OutboxEvent, error: str) -> None:
    event.attempts += 1
    event.last_error = error[:2000]
    now: datetime = get_clock().now()
    if event.attempts >= MAX_ATTEMPTS:
        event.status = OutboxEvent.Status.DEAD
    else:
        event.next_attempt_at = now + backoff_for(event.attempts)
    event.save(update_fields=["attempts", "last_error", "status", "next_attempt_at"])
