from decimal import Decimal

import pytest

from maud.shared.errors import DomainError
from maud.shared.shares import Shares, SharesPrecisionError


def test_accepts_up_to_eight_decimal_places() -> None:
    assert Shares.of("1.12345678").value == Decimal("1.12345678")


def test_rejects_ninth_decimal_instead_of_rounding_silently() -> None:
    with pytest.raises(SharesPrecisionError):
        Shares.of("1.123456789")


def test_rejects_float() -> None:
    with pytest.raises(TypeError):
        Shares.of(0.1)  # type: ignore[arg-type]


def test_truncate_rounds_down_to_never_over_issue() -> None:
    assert Shares.truncate(Decimal("10") / Decimal("3")) == Shares.of("3.33333333")


def test_addition_and_subtraction_preserve_precision() -> None:
    assert Shares.of("0.00000001") + Shares.of("0.00000002") == Shares.of("0.00000003")
    assert (Shares.of("1") - Shares.of("2")).is_negative


def test_percentage_is_derived_from_total() -> None:
    assert Shares.of("25").ratio_to(Shares.of("100")) == Decimal("0.25")


def test_percentage_of_zero_total_is_business_error() -> None:
    with pytest.raises(DomainError):
        Shares.of("1").ratio_to(Shares.zero())
