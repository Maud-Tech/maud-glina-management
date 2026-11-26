"""Corridas reais no Postgres: vários pedidos IGUAIS ao mesmo tempo produzem UM efeito."""

import threading

import pytest
from django.db import connection

from maud.modules.example.features.create_item.handler import CreateItemCommand, execute
from maud.modules.example.models import Item
from maud.shared.models import OutboxEvent

pytestmark = pytest.mark.django_db(transaction=True)

PARALLEL = 8


def test_same_key_in_parallel_creates_once_and_all_get_same_response() -> None:
    barrier = threading.Barrier(PARALLEL)
    results: list[str] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            barrier.wait()
            command = CreateItemCommand(name="Item A", idempotency_key="same")
            out = execute(command)
            results.append(str(out.id))
        except BaseException as exc:
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(PARALLEL)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(set(results)) == 1
    assert Item.objects.count() == 1
    assert OutboxEvent.objects.count() == 1
