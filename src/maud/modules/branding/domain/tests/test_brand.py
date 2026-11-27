import pytest

from maud.modules.branding.domain.brand import (
    DARK_TEXT,
    LIGHT_TEXT,
    MAX_NAME_LENGTH,
    contrast_ratio,
    initials,
    parse_brand_color,
    validate_name,
)
from maud.shared.errors import DomainError


def test_name_is_trimmed_and_inner_spaces_collapsed() -> None:
    assert validate_name("  Gestora   Exemplo ") == "Gestora Exemplo"


@pytest.mark.parametrize("empty", ["", "   "])
def test_empty_name_is_accepted_as_blank(empty: str) -> None:
    """O nome é opcional: a gestora pode ter só o logotipo."""
    assert validate_name(empty) == ""


def test_name_too_long_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_name("x" * (MAX_NAME_LENGTH + 1))
    assert error.value.code == "brand_name_too_long"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("#22bec6", "#22BEC6"), ("22BEC6", "#22BEC6"), (" #0f0 ", "#00FF00")],
)
def test_color_is_normalized_to_uppercase_six_digits(raw: str, expected: str) -> None:
    assert parse_brand_color(raw).value == expected


@pytest.mark.parametrize("raw", ["", "#12345", "azul", "#GGGGGG", "rgb(0,0,0)"])
def test_color_outside_hex_format_is_rejected(raw: str) -> None:
    with pytest.raises(DomainError) as error:
        parse_brand_color(raw)
    assert error.value.code == "brand_color_invalid"


def test_light_color_gets_dark_text() -> None:
    assert parse_brand_color("#22BEC6").text_on_color == DARK_TEXT


def test_dark_color_gets_light_text() -> None:
    assert parse_brand_color("#1E3A8A").text_on_color == LIGHT_TEXT


def test_mid_gray_where_no_text_is_readable_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        parse_brand_color("#787878")
    assert error.value.code == "brand_color_unreadable"


@pytest.mark.parametrize(
    "swatch", ["#22BEC6", "#3B82F6", "#10B981", "#8B5CF6", "#F97316", "#E11D48"]
)
def test_every_suggested_swatch_is_accepted(swatch: str) -> None:
    color = parse_brand_color(swatch)
    assert contrast_ratio(color.value, color.text_on_color) >= 4.5


def test_contrast_of_black_and_white_is_21() -> None:
    assert round(contrast_ratio("#000000", "#FFFFFF"), 2) == 21.0


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Gestora Exemplo", "GE"), ("Maud", "MA"), ("  ", "?"), ("Alfa & Beta", "AB")],
)
def test_initials_come_from_first_two_words(name: str, expected: str) -> None:
    assert initials(name) == expected
