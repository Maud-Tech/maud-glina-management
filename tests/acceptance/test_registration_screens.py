"""Fluxos reais de cadastro: listas separadas, permissões e gravação atômica."""

import uuid
from decimal import Decimal

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from maud.modules.assets.models import Asset, CashAsset, DebtInstrument, Equity, Fund, GenericAsset
from maud.modules.entities.models import Country, Currency, Entity, EntityCompany, EntityPerson
from maud.shared.models import IdempotencyRecord

pytestmark = pytest.mark.django_db

ROUTES = [
    ("entities", "currencies"),
    ("entities", "countries"),
    ("entities", "people"),
    ("entities", "addresses"),
    ("entities", "contacts"),
    ("assets", "assets"),
    ("assets", "venues"),
    ("assets", "identifiers"),
    ("assets", "listings"),
    ("assets", "classifications"),
    ("assets", "prices"),
    ("assets", "events"),
]


@pytest.fixture
def operator(client):
    user = User.objects.create_superuser(username="operator", password="test-only-password")
    client.force_login(user)
    return client


@pytest.fixture
def country():
    currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    return Country.objects.create(code="US", name="United States", currency=currency)


def submit(client, module, resource, data, *, pk=None, variant=""):
    suffix = "edit" if pk else "new"
    url = reverse(module + "_" + resource + "_" + suffix, args=[pk] if pk else [])
    response = client.get(url, {"variant": variant})
    assert response.status_code == 200
    payload = {"request_key": response.context["request_key"], "variant": variant, **data}
    return client.post(url, payload), payload, url


@pytest.mark.parametrize(("module", "resource"), ROUTES)
def test_registration_pages_require_login(client, module, resource):
    assert client.get(reverse(module + "_" + resource + "_list")).status_code == 302
    assert client.get(reverse(module + "_" + resource + "_new")).status_code == 302


@pytest.mark.parametrize(("module", "resource"), ROUTES)
def test_lists_are_separate_and_forms_return_to_their_own_list(operator, module, resource):
    list_url = reverse(module + "_" + resource + "_list")
    new_url = reverse(module + "_" + resource + "_new")
    listing = operator.get(list_url)
    assert listing.status_code == 200
    assert new_url in listing.content.decode()
    assert '<form method="post"' not in listing.content.decode().replace(
        '<form class="inline-form" method="post"', ""
    )
    form = operator.get(new_url)
    assert form.status_code == 200
    assert form.context["list_url"] == list_url
    assert form.content.decode().count('href="' + list_url + '"') >= 2


def test_entity_person_creates_matching_details_and_returns_to_people(operator):
    response, payload, url = submit(
        operator,
        "entities",
        "people",
        {
            "main-display_name": "Alice",
            "detail-full_name": "Alice Example",
        },
        variant="PERSON",
    )
    assert response.status_code == 302
    assert response.url == reverse("entities_people_list")
    person = Entity.objects.get(display_name="Alice")
    assert person.entity_kind == "PERSON"
    assert EntityPerson.objects.filter(entity=person).exists()
    assert not EntityCompany.objects.filter(entity=person).exists()
    assert operator.post(url, payload).status_code == 302
    assert Entity.objects.count() == 1


def test_entity_company_requires_registration_and_preserves_values(operator, country):
    data = {
        "main-display_name": "Atlas",
        "detail-legal_name": "Atlas LLC",
        "detail-incorporation_country": country.pk,
    }
    response, _, _ = submit(operator, "entities", "people", data, variant="COMPANY")
    assert response.status_code == 422
    assert Entity.objects.count() == 0
    data.update({"main-registration_country": country.pk, "main-registration_number": "98-123/4"})
    response, _, _ = submit(operator, "entities", "people", data, variant="COMPANY")
    assert response.status_code == 302
    entity = Entity.objects.get()
    assert entity.registration_number == "98-123/4"
    assert entity.company_details.legal_name == "Atlas LLC"


@pytest.mark.parametrize("family", ["EQUITY", "DEBT", "FUND", "CASH", "GENERIC"])
def test_asset_creates_exactly_one_matching_family_detail(operator, country, family):
    details = {
        "EQUITY": {"detail-equity_type": "COMMON_STOCK"},
        "DEBT": {
            "detail-instrument_type": "BOND",
            "detail-debt_type": "SOVEREIGN",
            "detail-coupon_type": "FIXED",
            "detail-maturity_date": "2034-01-01",
            "detail-coupon_rate": "4.25",
        },
        "FUND": {
            "detail-fund_type": "ETF",
            "detail-fund_name": "Fund",
            "detail-domicile_country": country.pk,
            "detail-distribution_policy": "ACCUMULATING",
        },
        "CASH": {},
        "GENERIC": {"detail-raw_data": '{"description": "Asset pending review"}'},
    }
    data = {
        "main-name": "Example",
        "main-short_name": "EX",
        "main-currency": "USD",
        "main-market_type": "OTC",
        "main-status": "ACTIVE",
        **details[family],
    }
    if family == "GENERIC":
        data["detail-normalization_status"] = "PENDING"
    response, payload, url = submit(operator, "assets", "assets", data, variant=family)
    assert response.status_code == 302, response.content.decode()
    assert response.url == reverse("assets_assets_list")
    asset = Asset.objects.get()
    assert asset.asset_family == family
    assert (
        sum(
            model.objects.count()
            for model in (Equity, DebtInstrument, Fund, CashAsset, GenericAsset)
        )
        == 1
    )
    if family == "DEBT":
        assert asset.debt_details.coupon_rate == Decimal("4.25")
    if family == "CASH":
        assert asset.cash_details.currency_id == asset.currency_id
    assert operator.post(url, payload).status_code == 302
    assert Asset.objects.count() == 1


def test_edit_keeps_entity_kind_fixed_and_returns_to_people(operator):
    entity = Entity.objects.create(entity_kind="PERSON", display_name="Before")
    EntityPerson.objects.create(entity=entity, full_name="Before")
    response, _, _ = submit(
        operator,
        "entities",
        "people",
        {
            "main-entity_kind": "COMPANY",
            "main-display_name": "After",
            "detail-full_name": "After",
        },
        pk=str(entity.pk),
        variant="COMPANY",
    )
    assert response.status_code == 302
    assert response.url == reverse("entities_people_list")
    entity.refresh_from_db()
    assert entity.entity_kind == "PERSON"
    assert entity.person_details.full_name == "After"


def test_write_requires_permission_even_when_url_is_known(client):
    user = User.objects.create_user("reader")
    user.user_permissions.add(Permission.objects.get(codename="view_currency"))
    client.force_login(user)
    assert client.get(reverse("entities_currencies_list")).status_code == 200
    response = client.post(
        reverse("entities_currencies_new"),
        {
            "main-code": "EUR",
            "main-name": "Euro",
            "request_key": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 403
    assert not Currency.objects.exists()


def test_invalid_debt_rolls_back_identity_and_idempotency(operator, country):
    response, _, _ = submit(
        operator,
        "assets",
        "assets",
        {
            "main-name": "Invalid",
            "main-short_name": "BAD",
            "main-currency": "USD",
            "main-market_type": "OTC",
            "main-status": "ACTIVE",
            "detail-instrument_type": "BOND",
            "detail-debt_type": "SOVEREIGN",
            "detail-coupon_type": "FIXED",
            "detail-issue_date": "2030-01-01",
            "detail-maturity_date": "2020-01-01",
        },
        variant="DEBT",
    )
    assert response.status_code == 422
    assert not Asset.objects.exists()
    assert not IdempotencyRecord.objects.exists()


def test_lists_filter_and_paginate(operator):
    Currency.objects.bulk_create(
        [Currency(code=str(i).zfill(3), name="Currency " + str(i), symbol="$") for i in range(30)]
    )
    response = operator.get(reverse("entities_currencies_list"))
    assert len(response.context["rows"]) == 25
    filtered = operator.get(reverse("entities_currencies_list"), {"q": "Currency 29"})
    assert len(filtered.context["rows"]) == 1
    assert filtered.context["page"].paginator.count == 1


def test_related_contacts_are_filtered_by_person(operator):
    first = Entity.objects.create(display_name="First", entity_kind="PERSON")
    second = Entity.objects.create(display_name="Second", entity_kind="PERSON")
    from maud.modules.entities.models import EntityContact

    EntityContact.objects.create(entity=first, contact_type="EMAIL", value="first@example.com")
    EntityContact.objects.create(entity=second, contact_type="EMAIL", value="second@example.com")
    response = operator.get(reverse("entities_contacts_list"), {"parent": str(first.pk)})
    assert len(response.context["rows"]) == 1
    assert "first@example.com" in response.content.decode()
    assert "second@example.com" not in response.content.decode()


@pytest.fixture
def asset(country):
    return Asset.objects.create(
        name="Example Asset",
        short_name="EX",
        currency=country.currency,
        asset_family="EQUITY",
        market_type="LISTED",
    )


@pytest.mark.parametrize(
    ("module", "resource", "fields"),
    [
        (
            "entities",
            "currencies",
            {
                "main-code": "EUR",
                "main-name": "Euro",
                "main-symbol": "€",
                "main-decimal_places": "2",
                "main-active": "on",
            },
        ),
        (
            "entities",
            "countries",
            {"main-code": "BR", "main-name": "Brasil", "main-currency": "USD"},
        ),
        ("assets", "venues", {"main-code": "NYSE", "main-name": "NYSE", "main-country": "US"}),
    ],
)
def test_auxiliary_registrations_save_and_return_to_own_list(
    operator, country, module, resource, fields
):
    response, payload, url = submit(operator, module, resource, fields)
    assert response.status_code == 302, (
        response.context["bundle"].main.errors if response.context else ""
    )
    assert response.url == reverse(module + "_" + resource + "_list")
    assert operator.post(url, payload).status_code == 302


def test_price_and_event_use_correct_labels_and_validate_unique_values(operator, asset):
    from maud.modules.assets.models import AssetEvent, AssetPrice

    fields = {
        "main-asset": str(asset.pk),
        "main-price_date": "2026-11-27",
        "main-price": "123.456789012345",
        "main-currency": "USD",
        "main-price_type": "MD",
    }
    response, _, _ = submit(operator, "assets", "prices", fields)
    assert response.status_code == 302
    assert AssetPrice.objects.get().price == Decimal("123.456789012345")
    duplicate, _, _ = submit(operator, "assets", "prices", fields)
    assert duplicate.status_code == 422
    assert AssetPrice.objects.count() == 1
    response, _, _ = submit(
        operator,
        "assets",
        "events",
        {
            "main-asset": str(asset.pk),
            "main-event_type": "DIVIDEND",
            "main-event_date": "2026-11-27",
            "main-cum_price": "100",
            "main-amount_paid": "1.25",
            "main-event_status": "EXPECTED",
        },
    )
    assert response.status_code == 302
    assert AssetEvent.objects.get().cum_price == Decimal("100")
    form = operator.get(reverse("assets_events_new"))
    assert "Preço COM" in form.content.decode()
    assert "Data COM" in form.content.decode()


@pytest.mark.parametrize(
    ("resource", "fields"),
    [
        ("identifiers", {"main-identifier_type": "ISIN", "main-value": "US0378331005"}),
        (
            "classifications",
            {
                "main-asset_class": "EQUITY",
                "main-liquidity_type": "DAYS",
                "main-liquidity_days": "2",
                "main-classification_source": "MANUAL",
            },
        ),
    ],
)
def test_asset_relationships_can_be_registered(operator, asset, resource, fields):
    response, _, _ = submit(
        operator,
        "assets",
        resource,
        {
            "main-asset": str(asset.pk),
            **fields,
        },
    )
    assert response.status_code == 302, response.content.decode()
    assert response.url == reverse("assets_" + resource + "_list")


def test_primary_contact_uniqueness_preserves_existing_value(operator):
    entity = Entity.objects.create(entity_kind="PERSON", display_name="Alice")
    fields = {
        "main-entity": str(entity.pk),
        "main-contact_type": "EMAIL",
        "main-value": "alice@example.com",
        "main-is_primary": "on",
    }
    response, _, _ = submit(operator, "entities", "contacts", fields)
    assert response.status_code == 302
    response, _, _ = submit(
        operator,
        "entities",
        "contacts",
        {
            **fields,
            "main-value": "other@example.com",
        },
    )
    assert response.status_code == 422
    assert entity.contacts.get().value == "alice@example.com"


def test_cash_uniqueness_rolls_back_second_asset(operator, country):
    fields = {
        "main-name": "Cash",
        "main-short_name": "USD",
        "main-currency": "USD",
        "main-market_type": "NOT_APPLICABLE",
        "main-status": "ACTIVE",
    }
    first, _, _ = submit(operator, "assets", "assets", fields, variant="CASH")
    assert first.status_code == 302
    second, _, _ = submit(operator, "assets", "assets", fields, variant="CASH")
    assert second.status_code == 422
    assert Asset.objects.count() == 1
    assert CashAsset.objects.count() == 1


def test_invalid_parent_filter_and_invalid_record_id_do_not_raise_server_error(operator):
    response = operator.get(reverse("entities_contacts_list"), {"parent": "invalid-uuid"})
    assert response.status_code == 200
    assert not response.context["rows"]
    assert operator.get(reverse("entities_people_edit", args=["invalid-uuid"])).status_code == 404


def test_read_only_user_can_open_but_cannot_submit_existing_record(client):
    user = User.objects.create_user("view-only")
    user.user_permissions.add(Permission.objects.get(codename="view_currency"))
    currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    client.force_login(user)
    url = reverse("entities_currencies_edit", args=[currency.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert not response.context["can_edit"]
    assert "Salvar cadastro" not in response.content.decode()
    assert client.post(url, {"main-name": "Changed"}).status_code == 403


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_registration_forms_render_both_themes(operator, theme):
    operator.cookies["theme"] = theme
    response = operator.get(reverse("entities_people_new"))
    assert 'data-theme="' + theme + '"' in response.content.decode()
    assert response.status_code == 200
