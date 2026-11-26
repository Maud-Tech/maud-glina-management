import pytest
from django.db import transaction
from pydantic import BaseModel

from maud.shared import outbox
from maud.shared.idempotency import IdempotencyConflictError, run_idempotent
from maud.shared.models import IdempotencyRecord, OutboxEvent

pytestmark = pytest.mark.django_db


class Out(BaseModel):
    value: int


def _op(value: int) -> Out:
    outbox.publish("test.happened", aggregate_type="t", aggregate_id="1", payload={"v": value})
    return Out(value=value)


def _run(key: str, value: int) -> Out:
    return run_idempotent(
        scope="test",
        key=key,
        request={"value": value},
        response_model=Out,
        operation=lambda: _op(value),
    )


def test_repeat_returns_same_response_without_rerunning() -> None:
    assert _run("k1", 7) == Out(value=7)
    assert _run("k1", 7) == Out(value=7)
    assert OutboxEvent.objects.count() == 1


def test_same_key_with_different_payload_is_conflict() -> None:
    _run("k2", 1)
    with pytest.raises(IdempotencyConflictError):
        _run("k2", 2)


def test_failed_operation_does_not_store_key() -> None:
    def boom() -> Out:
        raise RuntimeError("falhou")

    with pytest.raises(RuntimeError), transaction.atomic():
        run_idempotent(scope="test", key="k3", request={}, response_model=Out, operation=boom)
    assert not IdempotencyRecord.objects.filter(key="k3").exists()
