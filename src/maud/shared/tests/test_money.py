from decimal import ROUND_DOWN, Decimal

import pytest

from maud.shared.money import Currency, CurrencyMismatchError, Money, MoneyPrecisionError


def test_adds_same_currency() -> None:
    assert Money.of("10.10", "USD") + Money.of("0.90", "USD") == Money.of("11.00", "USD")


def test_different_currencies_do_not_mix() -> None:
    with pytest.raises(CurrencyMismatchError):
        Money.of("1", "USD") + Money.of("1", "BRL")


def test_rejects_more_decimals_than_currency_allows() -> None:
    with pytest.raises(MoneyPrecisionError):
        Money.of("1.001", "USD")


def test_rounding_is_explicit() -> None:
    assert Money.rounded(Decimal("1.005"), Currency.USD) == Money.of("1.00", "USD")
    assert Money.rounded(Decimal("1.019"), Currency.USD, ROUND_DOWN) == Money.of("1.01", "USD")


def test_rejects_float() -> None:
    with pytest.raises(TypeError):
        Money.of(1.5, "USD")  # type: ignore[arg-type]
