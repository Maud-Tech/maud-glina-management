from datetime import UTC, datetime, timedelta

import pytest
from django.db import transaction

from maud.shared import outbox
from maud.shared.clock import FixedClock, use_clock
from maud.shared.models import OutboxEvent

pytestmark = pytest.mark.django_db(transaction=True)

T0 = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


def _publish() -> OutboxEvent:
    with transaction.atomic():
        return outbox.publish("test.happened", aggregate_type="t", aggregate_id="1", payload={})


def test_publish_outside_transaction_is_forbidden() -> None:
    with pytest.raises(RuntimeError):
        outbox.publish("test.happened", aggregate_type="t", aggregate_id="1", payload={})


def test_failure_reschedules_with_backoff_and_dies_at_limit() -> None:
    clock = FixedClock(T0)
    with use_clock(clock):
        event = _publish()
        with transaction.atomic():
            outbox.mark_failed(event, "timeout")
        event.refresh_from_db()
        assert event.next_attempt_at == T0 + timedelta(seconds=30)

        with transaction.atomic():
            assert outbox.claim_batch() == []  # ainda não venceu

        for _ in range(outbox.MAX_ATTEMPTS):
            outbox.mark_failed(event, "timeout")
        assert event.status == OutboxEvent.Status.DEAD


def test_claim_returns_only_due_events_and_mark_sent_finalizes() -> None:
    with use_clock(FixedClock(T0)):
        event = _publish()
        with transaction.atomic():
            claimed = outbox.claim_batch()
            assert [e.id for e in claimed] == [event.id]
            outbox.mark_sent(claimed[0])
        with transaction.atomic():
            assert outbox.claim_batch() == []
