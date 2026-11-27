from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

from maud.modules.products.features.get_product.handler import GetProductQuery, execute
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
from maud.modules.products.responses import MandateResponse, PolicyResponse, ProductResponse
from maud.modules.products.testing import COMPLETE_TERMS, TODAY
from maud.shared.errors import NotFoundError

pytestmark = pytest.mark.django_db


def new_version(actor: Any, product: ProductResponse, risk_level: int) -> MandateResponse:
    draft = start_mandate_draft(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id,
            mandate_id=draft.id,
            terms=replace(COMPLETE_TERMS, risk_level=risk_level),
        )
    )
    return draft


def test_detail_shows_current_upcoming_and_draft_versions(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    second = new_version(actor, product, risk_level=3)
    publish_mandate(
        PublishMandateCommand(
            actor_id=actor.id,
            mandate_id=second.id,
            effective_from=TODAY + timedelta(days=15),
            reason="comitê",
        )
    )
    third = new_version(actor, product, risk_level=4)

    detail = execute(GetProductQuery(product_id=product.id))

    assert detail.product.code == "GLINA-USD-01"
    assert detail.policy is not None and detail.policy.id == policy.id
    assert detail.current_mandate is not None and detail.current_mandate.version == 1
    assert detail.upcoming_mandate is not None and detail.upcoming_mandate.version == 2
    assert detail.draft_mandate is not None and detail.draft_mandate.id == third.id
    assert detail.documents == []


def test_unknown_product_is_not_found(db: None) -> None:
    with pytest.raises(NotFoundError) as error:
        execute(GetProductQuery(product_id=uuid4()))

    assert error.value.code == "product_not_found"
