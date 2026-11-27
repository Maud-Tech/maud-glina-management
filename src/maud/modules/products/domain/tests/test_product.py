from datetime import date

import pytest

from maud.modules.products.domain.product import (
    ActivationReadiness,
    ProductStatus,
    check_identity_change,
    check_status_change,
    status_after_policy_expired,
    validate_product,
)
from maud.shared.errors import DomainError

READY = ActivationReadiness(has_published_mandate=True, has_effective_policy=True)


def test_code_and_name_are_normalized() -> None:
    data = validate_product(
        code=" glina-usd-01 ",
        name="  Glina   USD ",
        description="  texto  ",
        launch_date=None,
        closing_date=None,
    )

    assert data.code == "GLINA-USD-01"
    assert data.name == "Glina USD"
    assert data.description == "texto"


@pytest.mark.parametrize("code", ["", "-ABC", "COM ESPACO", "A" * 51, "ÇÃO"])
def test_invalid_code_is_rejected(code: str) -> None:
    with pytest.raises(DomainError) as error:
        validate_product(code=code, name="X", description="", launch_date=None, closing_date=None)

    assert error.value.code == "product_code_invalid"


def test_closing_before_launch_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_product(
            code="P1",
            name="X",
            description="",
            launch_date=date(2026, 12, 1),
            closing_date=date(2026, 11, 30),
        )

    assert error.value.code == "product_dates_invalid"


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ProductStatus.DRAFT, ProductStatus.ACTIVE),
        (ProductStatus.DRAFT, ProductStatus.CLOSED),
        (ProductStatus.ACTIVE, ProductStatus.INACTIVE),
        (ProductStatus.INACTIVE, ProductStatus.ACTIVE),
        (ProductStatus.ACTIVE, ProductStatus.CLOSED),
        (ProductStatus.EXPIRED, ProductStatus.CLOSED),
    ],
)
def test_allowed_status_changes_pass(current: ProductStatus, target: ProductStatus) -> None:
    check_status_change(current, target, READY)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ProductStatus.CLOSED, ProductStatus.ACTIVE),
        (ProductStatus.EXPIRED, ProductStatus.ACTIVE),
        (ProductStatus.ACTIVE, ProductStatus.EXPIRED),
        (ProductStatus.DRAFT, ProductStatus.INACTIVE),
    ],
)
def test_forbidden_status_changes_are_rejected(
    current: ProductStatus, target: ProductStatus
) -> None:
    with pytest.raises(DomainError) as error:
        check_status_change(current, target, READY)

    assert error.value.code == "product_status_change_not_allowed"


def test_activation_requires_mandate_before_policy() -> None:
    nothing = ActivationReadiness(has_published_mandate=False, has_effective_policy=False)

    with pytest.raises(DomainError) as error:
        check_status_change(ProductStatus.DRAFT, ProductStatus.ACTIVE, nothing)

    assert error.value.code == "product_activation_requires_published_mandate"


def test_reactivation_also_requires_effective_policy() -> None:
    no_policy = ActivationReadiness(has_published_mandate=True, has_effective_policy=False)

    with pytest.raises(DomainError) as error:
        check_status_change(ProductStatus.INACTIVE, ProductStatus.ACTIVE, no_policy)

    assert error.value.code == "product_activation_requires_effective_policy"


def test_currency_cannot_change_while_policy_exists_even_in_draft() -> None:
    with pytest.raises(DomainError) as error:
        check_identity_change(
            ProductStatus.DRAFT, code_changed=False, currency_changed=True, has_policy=True
        )

    assert error.value.code == "product_currency_has_policy"


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (ProductStatus.ACTIVE, ProductStatus.EXPIRED),
        (ProductStatus.INACTIVE, ProductStatus.EXPIRED),
        (ProductStatus.DRAFT, ProductStatus.DRAFT),
        (ProductStatus.CLOSED, ProductStatus.CLOSED),
    ],
)
def test_policy_expiry_expires_only_active_or_inactive_products(
    current: ProductStatus, expected: ProductStatus
) -> None:
    assert status_after_policy_expired(current) is expected
