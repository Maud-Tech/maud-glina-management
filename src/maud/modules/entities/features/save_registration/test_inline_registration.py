"""Cadastro opcional de contatos e endereços junto da identidade."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from maud.modules.entities.models import Country, Currency, Entity, EntityCompany
from maud.modules.entities.registrations import COMPANY_SECTORS

pytestmark = pytest.mark.django_db


@pytest.fixture
def operator(client: Client) -> Client:
    user = User.objects.create_superuser("operator", password="test-only")
    client.force_login(user)
    currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    Country.objects.create(code="US", name="United States", currency=currency)
    return client


def payload(kind: str = "PERSON") -> dict[str, str]:
    fields = {
        "request_key": str(uuid.uuid4()),
        "variant": kind,
        "main-display_name": "Example",
        "detail-full_name": "Example Person",
        "addresses-TOTAL_FORMS": "1",
        "addresses-INITIAL_FORMS": "0",
        "contacts-TOTAL_FORMS": "1",
        "contacts-INITIAL_FORMS": "0",
    }
    if kind == "COMPANY":
        fields.update(
            {
                "main-registration_country": "US",
                "main-registration_number": "98-123/4",
                "detail-legal_name": "Example LLC",
                "detail-incorporation_country": "US",
                "detail-sector": "financials",
            }
        )
    return fields


@pytest.mark.parametrize("kind", ["PERSON", "COMPANY"])
def test_empty_inline_contacts_and_addresses_are_optional(operator: Client, kind: str) -> None:
    response = operator.post(reverse("entities_people_new"), payload(kind))
    assert response.status_code == 302
    person = Entity.objects.get()
    assert not person.contacts.exists()
    assert not person.addresses.exists()


@pytest.mark.parametrize("kind", ["PERSON", "COMPANY"])
def test_person_and_multiple_related_items_save_together(operator: Client, kind: str) -> None:
    fields = payload(kind)
    fields.update(
        {
            "addresses-0-address_type": "BUSINESS",
            "addresses-0-address_line_1": "Main Street 1",
            "addresses-0-locality": "New York",
            "addresses-0-country": "US",
            "addresses-0-is_primary": "on",
            "contacts-TOTAL_FORMS": "2",
            "contacts-0-contact_type": "EMAIL",
            "contacts-0-value": "hello@example.com",
            "contacts-0-is_primary": "on",
            "contacts-1-contact_type": "PHONE",
            "contacts-1-value": "+1 (212) 555-0100",
        }
    )
    url = reverse("entities_people_new")
    response = operator.post(url, fields)
    assert response.status_code == 302, response.content.decode()
    person = Entity.objects.get()
    assert person.addresses.get().locality == "New York"
    assert person.contacts.count() == 2
    assert person.contacts.get(contact_type="PHONE").value == "+1 (212) 555-0100"
    assert operator.post(url, fields).status_code == 302
    assert Entity.objects.count() == 1
    assert person.contacts.count() == 2


def test_partially_filled_contact_rejects_entire_registration(operator: Client) -> None:
    fields = payload()
    fields.update({"contacts-0-contact_type": "EMAIL", "contacts-0-value": "invalid"})
    response = operator.post(reverse("entities_people_new"), fields)
    assert response.status_code == 422
    assert not Entity.objects.exists()


def test_duplicate_primary_contact_is_rejected_before_saving(operator: Client) -> None:
    fields = payload()
    fields.update(
        {
            "contacts-TOTAL_FORMS": "2",
            "contacts-0-contact_type": "EMAIL",
            "contacts-0-value": "a@example.com",
            "contacts-0-is_primary": "on",
            "contacts-1-contact_type": "EMAIL",
            "contacts-1-value": "b@example.com",
            "contacts-1-is_primary": "on",
        }
    )
    response = operator.post(reverse("entities_people_new"), fields)
    assert response.status_code == 422
    assert not Entity.objects.exists()


def test_company_sector_rejects_values_outside_the_list(operator: Client) -> None:
    fields = payload("COMPANY")
    fields["detail-sector"] = "other"
    response = operator.post(reverse("entities_people_new"), fields)
    assert response.status_code == 422
    assert not EntityCompany.objects.exists()


def test_company_sector_contains_only_approved_choices(operator: Client) -> None:
    response = operator.get(reverse("entities_people_new"), {"variant": "COMPANY"})
    choices = response.context["bundle"].detail.fields["sector"].choices
    assert list(choices) == [("", "Selecione (opcional)"), *COMPANY_SECTORS]


def test_currency_decimal_places_is_not_editable_from_form(operator: Client) -> None:
    url = reverse("entities_currencies_new")
    response = operator.get(url)
    assert "decimal_places" not in response.context["bundle"].main.fields
    response = operator.post(
        url,
        {
            "request_key": str(uuid.uuid4()),
            "main-code": "EUR",
            "main-name": "Euro",
            "main-symbol": "€",
            "main-active": "on",
            "main-decimal_places": "8",
        },
    )
    assert response.status_code == 302
    assert Currency.objects.get(code="EUR").decimal_places == 2


def test_inline_edit_preserves_related_ids_and_allows_explicit_removal(operator: Client) -> None:
    fields = payload()
    fields.update(
        {
            "contacts-0-contact_type": "EMAIL",
            "contacts-0-value": "before@example.com",
        }
    )
    assert operator.post(reverse("entities_people_new"), fields).status_code == 302
    person = Entity.objects.get()
    contact = person.contacts.get()
    fields.update(
        {
            "request_key": str(uuid.uuid4()),
            "contacts-INITIAL_FORMS": "1",
            "contacts-0-id": str(contact.pk),
            "contacts-0-value": "after@example.com",
        }
    )
    edit_url = reverse("entities_people_edit", args=[person.pk])
    response = operator.post(edit_url, fields)
    assert response.status_code == 302, response.content.decode()
    contact.refresh_from_db()
    assert contact.value == "after@example.com"
    fields.update({"request_key": str(uuid.uuid4()), "contacts-0-DELETE": "on"})
    assert operator.post(edit_url, fields).status_code == 302
    assert not person.contacts.exists()


def test_inline_contact_rejects_editing_another_person_record(operator: Client) -> None:
    from maud.modules.entities.models import EntityContact

    first = Entity.objects.create(display_name="First", entity_kind="PERSON")
    second = Entity.objects.create(display_name="Second", entity_kind="PERSON")
    unrelated = EntityContact.objects.create(
        entity=second, contact_type="EMAIL", value="private@example.com"
    )
    fields = payload()
    fields.update(
        {
            "contacts-INITIAL_FORMS": "1",
            "contacts-0-id": str(unrelated.pk),
            "contacts-0-contact_type": "EMAIL",
            "contacts-0-value": "changed@example.com",
        }
    )
    response = operator.post(reverse("entities_people_edit", args=[first.pk]), fields)
    assert response.status_code == 422
    unrelated.refresh_from_db()
    assert unrelated.value == "private@example.com"


def test_inline_contact_add_requires_its_own_permission(operator: Client) -> None:
    from django.contrib.auth.models import Permission

    user = User.objects.create_user("person-editor")
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["add_entity", "view_entitycontact"])
    )
    operator.force_login(user)
    fields = payload()
    fields.update({"contacts-0-contact_type": "EMAIL", "contacts-0-value": "a@example.com"})
    response = operator.post(reverse("entities_people_new"), fields)
    assert response.status_code == 422
    assert not Entity.objects.exists()
