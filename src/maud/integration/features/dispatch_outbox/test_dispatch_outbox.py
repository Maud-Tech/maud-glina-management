from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from django.db import transaction
from django.test import override_settings

from maud.integration import jobs
from maud.integration.adapters.webhook.fake import FakeWebhookClient
from maud.integration.features.dispatch_outbox.handler import execute
from maud.shared import outbox
from maud.shared.clock import FixedClock, use_clock
from maud.shared.models import OutboxEvent

pytestmark = pytest.mark.django_db

START = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> Iterator[FixedClock]:
    with use_clock(FixedClock(START)) as fixed:
        yield fixed  # type: ignore[misc]


def publish_event(aggregate_id: str = "1") -> OutboxEvent:
    with transaction.atomic():
        return outbox.publish(
            "example.item_created",
            aggregate_type="item",
            aggregate_id=aggregate_id,
            payload={"name": "Item A"},
        )


@pytest.mark.usefixtures("clock")
def test_pending_event_is_delivered_and_marked_sent() -> None:
    event = publish_event()
    webhook = FakeWebhookClient()

    result = execute(webhook)

    assert result.sent == 1
    event.refresh_from_db()
    assert event.status == OutboxEvent.Status.SENT


@pytest.mark.usefixtures("clock")
def test_envelope_follows_contract() -> None:
    event = publish_event(aggregate_id="abc")
    webhook = FakeWebhookClient()

    execute(webhook)

    assert webhook.sent == [
        {
            "event_id": str(event.id),
            "event_type": "example.item_created",
            "occurred_at": START.isoformat(),
            "aggregate": {"type": "item", "id": "abc"},
            "payload": {"name": "Item A"},
        }
    ]


@pytest.mark.usefixtures("clock")
def test_delivery_failure_reschedules_without_losing_event() -> None:
    event = publish_event()
    webhook = FakeWebhookClient(failures_before_success=1)

    result = execute(webhook)

    assert result.failed == 1
    event.refresh_from_db()
    assert event.status == OutboxEvent.Status.PENDING
    assert event.attempts == 1
    assert event.next_attempt_at == START + timedelta(seconds=30)


def test_waiting_event_is_not_resent_before_its_time(clock: FixedClock) -> None:
    publish_event()
    webhook = FakeWebhookClient(failures_before_success=1)
    execute(webhook)  # falha e reagenda para daqui a 30 s

    clock.advance(timedelta(seconds=29))
    assert execute(webhook).sent == 0

    clock.advance(timedelta(seconds=1))
    assert execute(webhook).sent == 1


@pytest.mark.usefixtures("clock")
def test_one_failed_event_does_not_block_the_others() -> None:
    publish_event(aggregate_id="1")
    publish_event(aggregate_id="2")
    webhook = FakeWebhookClient(failures_before_success=1)

    result = execute(webhook)

    assert result.failed == 1
    assert result.sent == 1


@pytest.mark.usefixtures("clock")
def test_job_does_nothing_without_webhook_url() -> None:
    event = publish_event()

    with override_settings(WEBHOOK_URL=""):
        jobs.dispatch_outbox()

    event.refresh_from_db()
    assert event.status == OutboxEvent.Status.PENDING
    assert event.attempts == 0
