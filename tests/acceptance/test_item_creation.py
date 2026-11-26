"""Cadastro de item visto de fora: o que a operação e o parceiro observam.

Exemplo de cenário de aceitação. Copie a forma para as regras reais do projeto.
"""

from datetime import UTC, datetime, timedelta

import pytest

from maud.integration.adapters.webhook.fake import FakeWebhookClient
from maud.integration.features.dispatch_outbox.handler import execute as dispatch
from maud.shared.clock import FixedClock, use_clock
from maud.shared.models import OutboxEvent
from maud.shared.testing import ApiClient

pytestmark = pytest.mark.django_db


def test_partner_receives_single_event_even_when_request_is_repeated(api: ApiClient) -> None:
    assert (
        api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1").status_code
        == 201
    )
    assert (
        api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1").status_code
        == 201
    )

    assert OutboxEvent.objects.filter(event_type="example.item_created").count() == 1


def test_item_is_not_created_twice_with_different_spelling(api: ApiClient) -> None:
    assert (
        api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1").status_code
        == 201
    )
    assert (
        api.post("/example/items", {"name": "  item a "}, idempotency_key="pedido-2").status_code
        == 409
    )


def test_partner_receives_event_at_least_once_even_after_failures(api: ApiClient) -> None:
    clock = FixedClock(datetime(2026, 1, 5, 12, 0, tzinfo=UTC))
    webhook = FakeWebhookClient(failures_before_success=2)

    with use_clock(clock):
        api.post("/example/items", {"name": "Item A"})

        dispatch(webhook)  # 1ª tentativa falha
        clock.advance(timedelta(minutes=1))
        dispatch(webhook)  # 2ª tentativa falha
        clock.advance(timedelta(minutes=2))
        dispatch(webhook)  # 3ª tentativa entrega

    assert [event["event_type"] for event in webhook.sent] == ["example.item_created"]
