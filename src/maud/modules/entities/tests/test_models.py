import pytest
from django.db import IntegrityError, transaction

from maud.modules.entities.models import (
    Country,
    Currency,
    Entity,
    EntityAddress,
    EntityContact,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def usd() -> Currency:
    return Currency.objects.create(code="USD", name="US Dollar", symbol="US$")


@pytest.fixture
def united_states(usd: Currency) -> Country:
    return Country.objects.create(code="US", name="United States", currency=usd)


@pytest.fixture
def company(united_states: Country) -> Entity:
    return Entity.objects.create(
        entity_kind=Entity.Kind.COMPANY,
        display_name="Example Company",
        registration_country=united_states,
        registration_number="123456",
    )


def test_country_references_its_currency(united_states: Country, usd: Currency) -> None:
    assert united_states.currency == usd


@pytest.mark.parametrize(
    ("country_is_set", "registration_number"),
    [(True, ""), (False, "123456")],
)
def test_incomplete_registration_is_rejected(
    united_states: Country,
    country_is_set: bool,
    registration_number: str,
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Entity.objects.create(
            entity_kind=Entity.Kind.PERSON,
            display_name="Example Person",
            registration_country=united_states if country_is_set else None,
            registration_number=registration_number,
        )


def test_duplicate_country_and_registration_is_rejected(
    united_states: Country,
    company: Entity,
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Entity.objects.create(
            entity_kind=Entity.Kind.COMPANY,
            display_name="Duplicate Company",
            registration_country=united_states,
            registration_number=company.registration_number,
        )


def test_multiple_entities_without_registration_are_allowed() -> None:
    Entity.objects.create(entity_kind=Entity.Kind.PERSON, display_name="First Person")
    Entity.objects.create(entity_kind=Entity.Kind.PERSON, display_name="Second Person")

    assert Entity.objects.count() == 2


def test_second_primary_address_of_same_type_is_rejected(
    company: Entity,
    united_states: Country,
) -> None:
    address = {
        "entity": company,
        "address_type": EntityAddress.Type.BUSINESS,
        "address_line_1": "First Avenue",
        "locality": "New York",
        "country": united_states,
        "is_primary": True,
    }
    EntityAddress.objects.create(**address)

    with pytest.raises(IntegrityError), transaction.atomic():
        EntityAddress.objects.create(**address)


def test_second_primary_contact_of_same_type_is_rejected(company: Entity) -> None:
    EntityContact.objects.create(
        entity=company,
        contact_type=EntityContact.Type.EMAIL,
        value="first@example.com",
        is_primary=True,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        EntityContact.objects.create(
            entity=company,
            contact_type=EntityContact.Type.EMAIL,
            value="second@example.com",
            is_primary=True,
        )
