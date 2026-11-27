"""Regras puras da identidade da gestora: sem banco, sem Django.

A gestora escolhe uma cor só. O texto que vai em cima dela (botão, etapa atual) é escuro ou
branco, o que der mais contraste; cor em que nenhum dos dois fica legível é recusada.
Legível = contraste de pelo menos 4,5:1 (WCAG AA para texto normal).
"""

import re
from dataclasses import dataclass
from decimal import Decimal

from maud.shared.errors import DomainError

DEFAULT_NAME = "Gestão de apólices"
DEFAULT_BRAND_COLOR = "#22BEC6"
DARK_TEXT = "#031011"
LIGHT_TEXT = "#FFFFFF"
MIN_TEXT_CONTRAST = Decimal("4.5")
MAX_NAME_LENGTH = 120

_HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class BrandColor:
    """Cor validada: `value` em #RRGGBB maiúsculo e o texto que fica legível em cima dela."""

    value: str
    text_on_color: str


def validate_name(name: str) -> str:
    """Nome da gestora sem espaços sobrando. Opcional (o logotipo pode já trazer o nome)."""
    clean = " ".join(name.split())
    if len(clean) > MAX_NAME_LENGTH:
        raise DomainError(
            f"O nome passa de {MAX_NAME_LENGTH} caracteres.", code="brand_name_too_long"
        )
    return clean


def parse_brand_color(raw: str) -> BrandColor:
    """Aceita #RGB ou #RRGGBB (com ou sem #) e escolhe o texto de maior contraste."""
    match = _HEX_COLOR.match(raw.strip())
    if match is None:
        raise DomainError("Use uma cor em hexadecimal, como #22BEC6.", code="brand_color_invalid")
    digits = match.group(1).upper()
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    value = f"#{digits}"

    on_dark_text = contrast_ratio(value, DARK_TEXT)
    on_light_text = contrast_ratio(value, LIGHT_TEXT)
    best_text, best_ratio = (
        (DARK_TEXT, on_dark_text) if on_dark_text >= on_light_text else (LIGHT_TEXT, on_light_text)
    )
    if best_ratio < MIN_TEXT_CONTRAST:
        raise DomainError(
            "Nessa cor o texto do botão fica ilegível. Escolha uma cor mais clara ou mais escura.",
            code="brand_color_unreadable",
        )
    return BrandColor(value=value, text_on_color=best_text)


def initials(name: str) -> str:
    """Duas letras para o lugar do logotipo enquanto não há imagem."""
    words = [word for word in name.split() if word[:1].isalnum()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def contrast_ratio(first: str, second: str) -> Decimal:
    """Contraste entre duas cores #RRGGBB, de 1 (igual) a 21 (preto e branco)."""
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (lighter + _FLARE) / (darker + _FLARE)


_FLARE = Decimal("0.05")
_LINEAR_LIMIT = Decimal("0.04045")
_LINEAR_DIVISOR = Decimal("12.92")
_GAMMA_OFFSET = Decimal("0.055")
_GAMMA_SCALE = Decimal("1.055")
_GAMMA = Decimal("2.4")
_WEIGHTS = (Decimal("0.2126"), Decimal("0.7152"), Decimal("0.0722"))


def relative_luminance(color: str) -> Decimal:
    """Luminância relativa (WCAG 2) de uma cor #RRGGBB."""
    channels = [Decimal(int(color[index : index + 2], 16)) / 255 for index in (1, 3, 5)]
    linear = [
        channel / _LINEAR_DIVISOR
        if channel <= _LINEAR_LIMIT
        else ((channel + _GAMMA_OFFSET) / _GAMMA_SCALE) ** _GAMMA
        for channel in channels
    ]
    return sum((weight * value for weight, value in zip(_WEIGHTS, linear, strict=True)), Decimal(0))
