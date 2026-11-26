import pytest

from maud.modules.example.domain.item import MAX_NAME_LENGTH, NewItem, validate_new_item
from maud.shared.errors import DomainError


def test_collapses_repeated_spaces_and_trims_ends() -> None:
    assert validate_new_item(name="  Item   A ") == NewItem(name="Item A")


@pytest.mark.parametrize("empty_name", ["", "   "])
def test_name_is_required(empty_name: str) -> None:
    with pytest.raises(DomainError) as error:
        validate_new_item(name=empty_name)

    assert error.value.code == "item_name_required"


def test_name_too_long_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_new_item(name="x" * (MAX_NAME_LENGTH + 1))

    assert error.value.code == "item_name_too_long"
