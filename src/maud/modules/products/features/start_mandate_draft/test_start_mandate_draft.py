from typing import Any

import pytest

from maud.modules.products.features.start_mandate_draft.handler import (
    StartMandateDraftCommand,
    execute,
)
from maud.modules.products.models import MandateChange
from maud.modules.products.responses import MandateResponse, ProductResponse
from maud.shared.errors import ConflictError

pytestmark = pytest.mark.django_db


def test_first_draft_is_version_one_and_empty(actor: Any, product: ProductResponse) -> None:
    draft = execute(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))

    assert draft.version == 1
    assert draft.state == "DRAFT"
    assert draft.risk_level is None
    assert draft.exposure_limits == []
    change = MandateChange.objects.get()
    assert change.action == "CREATED"
    assert change.changes == {"version": [None, 1], "copied_from_version": [None, None]}


def test_new_draft_copies_latest_published_version_and_its_limits(
    actor: Any, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    draft = execute(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))

    assert draft.version == 2
    assert draft.state == "DRAFT"
    assert draft.effective_from is None
    assert draft.risk_level == published_mandate.risk_level
    assert draft.eligible_asset_classes == published_mandate.eligible_asset_classes
    assert [(item.dimension, item.target, item.max_pct) for item in draft.exposure_limits] == [
        (item.dimension, item.target, item.max_pct) for item in published_mandate.exposure_limits
    ]
    assert {item.id for item in draft.exposure_limits}.isdisjoint(
        {item.id for item in published_mandate.exposure_limits}
    )


def test_second_draft_while_one_is_open_is_rejected(
    actor: Any, product: ProductResponse, draft: MandateResponse
) -> None:
    with pytest.raises(ConflictError) as error:
        execute(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))

    assert error.value.code == "mandate_draft_exists"
