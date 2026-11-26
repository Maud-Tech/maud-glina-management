"""Dinheiro: valor Decimal + moeda. Operar moedas diferentes é erro; câmbio é conversão explícita.

A precisão segue a moeda (USD/BRL/EUR/GBP = 2 casas). Valores com mais casas são rejeitados;
para arredondar use `Money.rounded` dizendo a regra.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from maud.shared.errors import DomainError


class Currency(StrEnum):
    USD = "USD"
    BRL = "BRL"
    EUR = "EUR"
    GBP = "GBP"


MINOR_UNITS: dict[Currency, int] = {
    Currency.USD: 2,
    Currency.BRL: 2,
    Currency.EUR: 2,
    Currency.GBP: 2,
}


class MoneyPrecisionError(DomainError, ValueError):
    code = "money_precision"


class CurrencyMismatchError(DomainError, ValueError):
    code = "currency_mismatch"


def _quantum(currency: Currency) -> Decimal:
    return Decimal(1).scaleb(-MINOR_UNITS[currency])


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money exige Decimal, recebeu {type(self.amount).__name__}")
        if not self.amount.is_finite():
            raise MoneyPrecisionError("Valor precisa ser finito")
        quantum = _quantum(self.currency)
        if self.amount.quantize(quantum) != self.amount:
            raise MoneyPrecisionError(
                f"{self.amount} {self.currency} tem casas demais; use Money.rounded"
            )
        object.__setattr__(self, "amount", self.amount.quantize(quantum))

    @classmethod
    def of(cls, amount: Decimal | int | str, currency: Currency | str) -> Money:
        if isinstance(amount, bool) or not isinstance(amount, Decimal | int | str):
            raise TypeError(f"Money.of não aceita {type(amount).__name__}")
        return cls(Decimal(amount), Currency(currency))

    @classmethod
    def zero(cls, currency: Currency | str) -> Money:
        return cls(Decimal(0), Currency(currency))

    @classmethod
    def rounded(
        cls, amount: Decimal, currency: Currency | str, rounding: str = ROUND_HALF_EVEN
    ) -> Money:
        cur = Currency(currency)
        return cls(amount.quantize(_quantum(cur), rounding=rounding), cur)

    def _check(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"{self.currency} × {other.currency}: converta antes")

    def __add__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._check(other)
        return self.amount <= other.amount

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
