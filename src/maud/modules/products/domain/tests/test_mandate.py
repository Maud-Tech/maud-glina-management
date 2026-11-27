from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from maud.modules.products.domain.mandate import (
    LimitDimension,
    LimitTerms,
    MandateState,
    MandateTerms,
    check_draft,
    check_effective_date,
    check_publish_reason,
    check_publishable,
    validate_limits,
    validate_terms,
)
from maud.shared.errors import DomainError

CLASSES = frozenset({"EQUITY", "FIXED_INCOME", "CASH"})
COMPLETE = MandateTerms(
    risk_level=3,
    target_return_spread_pct=Decimal("2.5"),
    liquidity_days=30,
    max_average_term_years=Decimal("4"),
    eligible_asset_classes=("EQUITY",),
    min_initial_amount=Decimal("1000"),
    subscription_settlement_days=2,
    redemption_settlement_days=5,
)


def limit(
    dimension: LimitDimension = LimitDimension.ASSET_CLASS,
    target: str = "EQUITY",
    min_pct: str = "0",
    max_pct: str = "20",
) -> LimitTerms:
    return LimitTerms(dimension, target, Decimal(min_pct), Decimal(max_pct))


@pytest.mark.parametrize("risk_level", [0, 6])
def test_risk_level_outside_one_to_five_is_rejected(risk_level: int) -> None:
    with pytest.raises(DomainError) as error:
        validate_terms(MandateTerms(risk_level=risk_level), CLASSES)

    assert error.value.code == "mandate_risk_level_invalid"


def test_draft_may_be_incomplete() -> None:
    assert validate_terms(MandateTerms(), CLASSES) == MandateTerms()


def test_eligible_classes_are_normalized_and_unknown_class_is_rejected() -> None:
    terms = validate_terms(
        MandateTerms(eligible_asset_classes=(" equity", "CASH", "EQUITY")), CLASSES
    )
    assert terms.eligible_asset_classes == ("CASH", "EQUITY")

    with pytest.raises(DomainError) as error:
        validate_terms(MandateTerms(eligible_asset_classes=("CRYPTO",)), CLASSES)
    assert error.value.code == "mandate_asset_class_unknown"


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"target_return_spread_pct": Decimal("1.23456")}, "mandate_target_return_invalid"),
        ({"max_average_term_years": Decimal("0")}, "mandate_average_term_invalid"),
        ({"min_initial_amount": Decimal("-1")}, "mandate_amount_invalid"),
        ({"min_balance_amount": Decimal("10.001")}, "mandate_amount_invalid"),
        ({"lock_up_months": -1}, "mandate_term_invalid"),
    ],
)
def test_out_of_range_terms_are_rejected(changes: dict[str, object], code: str) -> None:
    with pytest.raises(DomainError) as error:
        validate_terms(replace(COMPLETE, **changes), CLASSES)  # type: ignore[arg-type]

    assert error.value.code == code


def test_incomplete_terms_cannot_be_published() -> None:
    with pytest.raises(DomainError) as error:
        check_publishable(replace(COMPLETE, risk_level=None, eligible_asset_classes=()))

    assert error.value.code == "mandate_incomplete"
    assert "risk_level" in error.value.message
    assert "eligible_asset_classes" in error.value.message


def test_complete_terms_can_be_published() -> None:
    check_publishable(COMPLETE)


def test_exposure_limit_with_min_above_max_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_limits([limit(min_pct="30", max_pct="20")], ("EQUITY",))

    assert error.value.code == "exposure_limit_range_invalid"


def test_exposure_limit_above_hundred_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_limits([limit(max_pct="100.01")], ("EQUITY",))

    assert error.value.code == "exposure_limit_range_invalid"


def test_asset_class_limit_outside_eligible_classes_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_limits([limit(target="CASH")], ("EQUITY",))

    assert error.value.code == "exposure_limit_asset_class_not_eligible"


def test_repeated_limit_for_same_dimension_and_target_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_limits([limit(), limit(target=" equity ")], ("EQUITY",))

    assert error.value.code == "exposure_limit_duplicated"


def test_single_asset_limit_has_no_target_and_others_need_one() -> None:
    assert validate_limits([limit(LimitDimension.SINGLE_ASSET, "")], ())

    with pytest.raises(DomainError) as error:
        validate_limits([limit(LimitDimension.SINGLE_ASSET, "X")], ())
    assert error.value.code == "exposure_limit_target_not_allowed"

    with pytest.raises(DomainError) as error:
        validate_limits([limit(LimitDimension.COUNTRY, " ")], ())
    assert error.value.code == "exposure_limit_target_required"


def test_limit_targets_are_normalized_by_dimension() -> None:
    issuer_id = "6F9619FF-8B86-D011-B42D-00CF4FC964FF"
    clean = validate_limits(
        [limit(LimitDimension.COUNTRY, " us"), limit(LimitDimension.ISSUER, issuer_id)], ()
    )

    assert [item.target for item in clean] == ["US", issuer_id.lower()]


def test_published_mandate_is_never_edited() -> None:
    with pytest.raises(DomainError) as error:
        check_draft(MandateState.PUBLISHED)

    assert error.value.code == "mandate_not_draft"


def test_new_version_must_start_after_previous_version() -> None:
    with pytest.raises(DomainError) as error:
        check_effective_date(date(2026, 12, 1), date(2026, 12, 1))

    assert error.value.code == "mandate_effective_date_not_after_previous"
    check_effective_date(date(2026, 12, 2), date(2026, 12, 1))
    check_effective_date(date(2020, 1, 1), None)


def test_reason_is_required_from_second_version_on() -> None:
    assert check_publish_reason(1, "  ") == ""
    assert check_publish_reason(2, " decisão do comitê ") == "decisão do comitê"

    with pytest.raises(DomainError) as error:
        check_publish_reason(2, "")
    assert error.value.code == "mandate_publish_reason_required"
