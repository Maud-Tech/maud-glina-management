"""Invariantes do kernel numérico, testadas com milhares de valores gerados."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from maud.shared.money import Money
from maud.shared.shares import Shares

shares_values = st.decimals(
    min_value=Decimal("-1e12"),
    max_value=Decimal("1e12"),
    places=8,
    allow_nan=False,
    allow_infinity=False,
).map(Shares)
money_values = st.decimals(
    min_value=Decimal("-1e12"),
    max_value=Decimal("1e12"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
).map(lambda d: Money(d, "USD"))  # type: ignore[arg-type]


@given(shares_values, shares_values)
def test_adding_then_subtracting_shares_returns_to_start(a: Shares, b: Shares) -> None:
    assert (a + b) - b == a


@given(st.lists(shares_values, max_size=50))
def test_shares_sum_is_order_independent(values: list[Shares]) -> None:
    forward = sum(values, Shares.zero())
    backward = sum(reversed(values), Shares.zero())
    assert forward == backward


@given(
    st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1e9"), places=2),
    st.decimals(min_value=Decimal("0.00000001"), max_value=Decimal("1e6"), places=8),
)
def test_converting_amount_to_shares_never_over_issues(amount: Decimal, price: Decimal) -> None:
    shares = Shares.truncate(amount / price)
    assert shares.value * price <= amount


@given(st.lists(money_values, max_size=50))
def test_money_sum_is_order_independent(values: list[Money]) -> None:
    forward = sum(values, Money.zero("USD"))
    backward = sum(reversed(values), Money.zero("USD"))
    assert forward == backward
