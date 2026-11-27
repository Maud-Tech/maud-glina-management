from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from maud.modules.products.domain.mandate import LimitDimension, LimitTerms
from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
    execute,
)
from maud.modules.products.models import ExposureLimit, MandateChange
from maud.modules.products.responses import MandateResponse
from maud.modules.products.testing import COMPLETE_TERMS, EQUITY_LIMIT
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db

US_LIMIT = LimitTerms(LimitDimension.COUNTRY, "US", Decimal("0"), Decimal("80"))


def update(
    actor: Any, draft: MandateResponse, *limits: LimitTerms, **terms: Any
) -> MandateResponse:
    return execute(
        UpdateMandateDraftCommand(
            actor_id=actor.id,
            mandate_id=draft.id,
            terms=replace(COMPLETE_TERMS, **terms),
            limits=limits,
        )
    )


def test_terms_are_saved_and_recorded_with_before_and_after(
    actor: Any, draft: MandateResponse
) -> None:
    saved = update(actor, draft)

    assert saved.risk_level == 2
    assert saved.target_return_benchmark == "SOFR"
    assert saved.target_return_spread_pct == Decimal("2")
    change = MandateChange.objects.get(action="UPDATED")
    assert change.changes["risk_level"] == [None, 2]
    assert change.changes["eligible_asset_classes"] == [[], ["EQUITY", "FIXED_INCOME"]]


def test_limit_added_changed_and_removed_are_each_recorded(
    actor: Any, draft: MandateResponse, united_states: Any
) -> None:
    update(actor, draft, EQUITY_LIMIT, US_LIMIT)
    removed_id = ExposureLimit.objects.get(dimension="COUNTRY").id

    update(actor, draft, replace(EQUITY_LIMIT, max_pct=Decimal("30")))

    limit_changes = MandateChange.objects.exclude(exposure_limit_id=None)
    assert sorted(limit_changes.values_list("action", flat=True)) == [
        "CREATED",
        "CREATED",
        "REMOVED",
        "UPDATED",
    ]
    removed = limit_changes.get(action="REMOVED")
    assert removed.exposure_limit_id == removed_id
    assert removed.changes["target"] == ["US", None]
    assert removed.changes["max_pct"] == ["80.00", None]
    assert limit_changes.get(action="UPDATED").changes == {"max_pct": ["20.00", "30"]}
    assert not ExposureLimit.objects.filter(pk=removed_id).exists()


def test_saving_same_terms_and_limits_records_nothing_new(
    actor: Any, draft: MandateResponse
) -> None:
    update(actor, draft, EQUITY_LIMIT)
    before = MandateChange.objects.count()

    update(actor, draft, EQUITY_LIMIT)

    assert MandateChange.objects.count() == before


def test_published_mandate_is_never_edited(actor: Any, published_mandate: MandateResponse) -> None:
    with pytest.raises(DomainError) as error:
        update(actor, published_mandate, risk_level=5)

    assert error.value.code == "mandate_not_draft"


def test_limit_on_asset_class_not_eligible_is_rejected(actor: Any, draft: MandateResponse) -> None:
    cash_limit = replace(EQUITY_LIMIT, target="CASH")

    with pytest.raises(DomainError) as error:
        update(actor, draft, cash_limit)

    assert error.value.code == "exposure_limit_asset_class_not_eligible"


def test_limit_on_unregistered_country_or_issuer_is_rejected(
    actor: Any, draft: MandateResponse, usd: Any
) -> None:
    with pytest.raises(DomainError) as error:
        update(actor, draft, US_LIMIT)
    assert error.value.code == "exposure_limit_target_not_found"

    issuer_limit = LimitTerms(LimitDimension.ISSUER, "not-an-id", Decimal("0"), Decimal("10"))
    with pytest.raises(DomainError) as error:
        update(actor, draft, issuer_limit)
    assert error.value.code == "exposure_limit_target_not_found"


def test_unknown_asset_class_is_rejected(actor: Any, draft: MandateResponse) -> None:
    with pytest.raises(DomainError) as error:
        update(actor, draft, eligible_asset_classes=("CRYPTO",))

    assert error.value.code == "mandate_asset_class_unknown"
