"""Quantidade de shares: Decimal com no máximo 8 casas. Nunca float nem arredondamento implícito.

Arredondar é sempre uma decisão explícita (ver `Shares.truncate`). O percentual de participação
NUNCA é guardado: é derivado com `ratio_to`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from maud.shared.errors import DomainError

SHARE_PLACES = 8
_QUANTUM = Decimal(1).scaleb(-SHARE_PLACES)  # 0.00000001


class SharesPrecisionError(DomainError, ValueError):
    code = "shares_precision"


@dataclass(frozen=True, slots=True, order=True)
class Shares:
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError(f"Shares exige Decimal, recebeu {type(self.value).__name__}")
        if not self.value.is_finite():
            raise SharesPrecisionError("Quantidade de shares precisa ser finita")
        quantized = self.value.quantize(_QUANTUM, rounding=ROUND_DOWN)
        if quantized != self.value:
            raise SharesPrecisionError(
                f"{self.value} tem mais de {SHARE_PLACES} casas; arredonde explicitamente"
            )
        object.__setattr__(self, "value", quantized)

    @classmethod
    def of(cls, value: Decimal | int | str) -> Shares:
        if isinstance(value, bool) or not isinstance(value, Decimal | int | str):
            raise TypeError(f"Shares.of não aceita {type(value).__name__}")
        return cls(Decimal(value))

    @classmethod
    def zero(cls) -> Shares:
        return cls(Decimal(0))

    @classmethod
    def truncate(cls, value: Decimal) -> Shares:
        """Arredonda PARA BAIXO em 8 casas: ao converter valor em shares, nunca emite a mais."""
        return cls(value.quantize(_QUANTUM, rounding=ROUND_DOWN))

    def __add__(self, other: Shares) -> Shares:
        return Shares(self.value + other.value)

    def __sub__(self, other: Shares) -> Shares:
        return Shares(self.value - other.value)

    def __neg__(self) -> Shares:
        return Shares(-self.value)

    @property
    def is_zero(self) -> bool:
        return self.value == 0

    @property
    def is_negative(self) -> bool:
        return self.value < 0

    def ratio_to(self, total: Shares) -> Decimal:
        """Fração (0..1) deste saldo sobre o total. Sem arredondar: quem exibe decide as casas."""
        if total.is_zero:
            raise DomainError("Total de shares é zero", code="zero_total_shares")
        return self.value / total.value

    def __str__(self) -> str:
        return f"{self.value:.{SHARE_PLACES}f}"
