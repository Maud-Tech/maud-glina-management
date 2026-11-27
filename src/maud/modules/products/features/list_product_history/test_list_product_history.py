from datetime import timedelta
from typing import Any

import pytest
from django.db import DatabaseError, transaction

from maud.modules.products.features.list_product_history.handler import (
    ListProductHistoryQuery,
    execute,
)
from maud.modules.products.features.publish_mandate.handler import PublishMandateCommand
from maud.modules.products.features.publish_mandate.handler import execute as publish_mandate
from maud.modules.products.features.start_mandate_draft.handler import StartMandateDraftCommand
from maud.modules.products.features.start_mandate_draft.handler import (
    execute as start_mandate_draft,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    execute as update_mandate_draft,
)
from maud.modules.products.models import MandateChange, ProductChange
from maud.modules.products.responses import ProductResponse
from maud.modules.products.testing import COMPLETE_TERMS, EQUITY_LIMIT, TODAY
from maud.shared.clock import FixedClock

pytestmark = pytest.mark.django_db


def test_timeline_merges_product_and_mandate_changes_newest_first(
    actor: Any, product: ProductResponse, clock: FixedClock
) -> None:
    clock.advance(timedelta(minutes=1))
    draft = start_mandate_draft(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))
    clock.advance(timedelta(minutes=1))
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id, mandate_id=draft.id, terms=COMPLETE_TERMS, limits=(EQUITY_LIMIT,)
        )
    )
    clock.advance(timedelta(minutes=1))
    publish_mandate(
        PublishMandateCommand(actor_id=actor.id, mandate_id=draft.id, effective_from=TODAY)
    )

    entries = execute(ListProductHistoryQuery(product_id=product.id))

    pairs = [(entry.object_type, entry.action) for entry in entries]
    assert pairs[0] == ("MANDATE", "PUBLISHED")
    # termos e limite gravados no mesmo instante: a ordem entre os dois não importa
    assert set(pairs[1:3]) == {("MANDATE", "UPDATED"), ("EXPOSURE_LIMIT", "CREATED")}
    assert pairs[3:] == [("MANDATE", "CREATED"), ("PRODUCT", "CREATED")]
    assert {entry.mandate_version for entry in entries[:4]} == {1}
    assert all(entry.changed_by == "operadora" for entry in entries)


def test_history_rows_cannot_be_changed_or_deleted(
    actor: Any, product: ProductResponse, draft: Any
) -> None:
    """Histórico é append-only: o banco recusa UPDATE e DELETE."""
    for model in (ProductChange, MandateChange):
        with pytest.raises(DatabaseError), transaction.atomic():
            model.objects.update(reason="reescrito")
        with pytest.raises(DatabaseError), transaction.atomic():
            model.objects.all().delete()
