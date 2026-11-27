from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from maud.modules.products.domain.mandate import MandateTerms
from maud.modules.products.features.publish_mandate.handler import PublishMandateCommand, execute
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
from maud.modules.products.models import Mandate, MandateChange
from maud.modules.products.responses import MandateResponse, ProductResponse
from maud.modules.products.testing import COMPLETE_TERMS, NOW, TODAY
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


def publish(
    actor: Any, mandate: MandateResponse, days: int = 0, reason: str = ""
) -> MandateResponse:
    return execute(
        PublishMandateCommand(
            actor_id=actor.id,
            mandate_id=mandate.id,
            effective_from=TODAY + timedelta(days=days),
            reason=reason,
        )
    )


def second_draft(actor: Any, product: ProductResponse) -> MandateResponse:
    return start_mandate_draft(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))


def test_publishing_sets_effective_date_author_and_history(
    actor: Any, published_mandate: MandateResponse
) -> None:
    assert published_mandate.state == "PUBLISHED"
    assert published_mandate.effective_from == TODAY
    assert published_mandate.published_at == NOW
    change = MandateChange.objects.get(action="PUBLISHED")
    assert change.changes == {
        "state": ["DRAFT", "PUBLISHED"],
        "effective_from": [None, TODAY.isoformat()],
    }


def test_incomplete_draft_cannot_be_published(actor: Any, draft: MandateResponse) -> None:
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id, mandate_id=draft.id, terms=MandateTerms(risk_level=3)
        )
    )

    with pytest.raises(DomainError) as error:
        publish(actor, draft)

    assert error.value.code == "mandate_incomplete"


def test_published_mandate_cannot_be_published_again(
    actor: Any, published_mandate: MandateResponse
) -> None:
    with pytest.raises(DomainError) as error:
        publish(actor, published_mandate, days=1)

    assert error.value.code == "mandate_not_draft"


def test_new_version_must_start_after_previous_and_needs_reason(
    actor: Any, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    draft = second_draft(actor, product)

    with pytest.raises(DomainError) as error:
        publish(actor, draft, days=0, reason="comitê")
    assert error.value.code == "mandate_effective_date_not_after_previous"

    with pytest.raises(DomainError) as error:
        publish(actor, draft, days=10)
    assert error.value.code == "mandate_publish_reason_required"

    published = publish(actor, draft, days=10, reason="decisão do comitê")
    assert published.version == 2
    assert MandateChange.objects.get(action="PUBLISHED", mandate_id=draft.id).reason == (
        "decisão do comitê"
    )


def test_second_version_keeps_first_version_untouched(
    actor: Any, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    draft = second_draft(actor, product)
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id, mandate_id=draft.id, terms=replace(COMPLETE_TERMS, risk_level=4)
        )
    )
    publish(actor, draft, days=10, reason="mais risco")

    first = Mandate.objects.get(pk=published_mandate.id)
    assert first.state == "PUBLISHED"
    assert first.risk_level == 2
    assert first.effective_from == TODAY
    assert Mandate.objects.get(pk=draft.id).risk_level == 4
