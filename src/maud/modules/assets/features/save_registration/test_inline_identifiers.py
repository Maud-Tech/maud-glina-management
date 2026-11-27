"""Identificadores opcionais no formulário de ativos, com gravação atômica."""

import uuid
from typing import Any

import pytest
from django.apps import apps
from django.contrib.auth.models import Permission, User
from django.test import Client
from django.urls import reverse

from maud.modules.assets.models import Asset, AssetIdentifier

pytestmark = pytest.mark.django_db


def currency_model() -> Any:
    return apps.get_model("entities", "Currency")


@pytest.fixture
def operator(client: Client) -> Client:
    user = User.objects.create_superuser("operator", password="test-only")
    client.force_login(user)
    currency_model().objects.create(code="USD", name="US Dollar", symbol="$")
    return client


def payload() -> dict[str, str]:
    return {
        "request_key": str(uuid.uuid4()),
        "variant": "EQUITY",
        "main-name": "Example",
        "main-short_name": "EX",
        "main-currency": "USD",
        "main-market_type": "LISTED",
        "main-status": "ACTIVE",
        "detail-equity_type": "COMMON_STOCK",
        "identifiers-TOTAL_FORMS": "1",
        "identifiers-INITIAL_FORMS": "0",
    }


def test_identifiers_are_embedded_and_not_in_navigation(operator: Client) -> None:
    response = operator.get(reverse("assets_assets_new"))
    html = response.content.decode()
    assert "Adicionar identificador" in html
    assert 'name="identifiers-TOTAL_FORMS"' in html
    assert 'href="/assets/identifiers/"' not in html


def test_empty_identifiers_do_not_block_asset_creation(operator: Client) -> None:
    response = operator.post(reverse("assets_assets_new"), payload())
    assert response.status_code == 302
    assert Asset.objects.count() == 1
    assert not AssetIdentifier.objects.exists()


def test_multiple_identifiers_save_with_asset_and_replay_once(operator: Client) -> None:
    fields = payload()
    fields.update(
        {
            "identifiers-TOTAL_FORMS": "2",
            "identifiers-0-identifier_type": "ISIN",
            "identifiers-0-value": "US0378331005",
            "identifiers-0-is_primary": "on",
            "identifiers-1-identifier_type": "CUSIP",
            "identifiers-1-value": "037833100",
        }
    )
    url = reverse("assets_assets_new")
    response = operator.post(url, fields)
    assert response.status_code == 302, response.content.decode()
    assert response["Location"] == reverse("assets_assets_list")
    assert Asset.objects.get().identifiers.count() == 2
    assert operator.post(url, fields).status_code == 302
    assert Asset.objects.count() == 1
    assert AssetIdentifier.objects.count() == 2


@pytest.mark.parametrize("duplicate", ["primary", "value"])
def test_duplicate_identifiers_reject_entire_asset(operator: Client, duplicate: str) -> None:
    fields = payload()
    fields.update(
        {
            "identifiers-TOTAL_FORMS": "2",
            "identifiers-0-identifier_type": "ISIN",
            "identifiers-0-value": "FIRST",
            "identifiers-0-is_primary": "on",
            "identifiers-1-identifier_type": "ISIN",
            "identifiers-1-value": "FIRST" if duplicate == "value" else "SECOND",
            "identifiers-1-is_primary": "on",
        }
    )
    response = operator.post(reverse("assets_assets_new"), fields)
    assert response.status_code == 422
    assert not Asset.objects.exists()
    assert not AssetIdentifier.objects.exists()


def test_incomplete_identifier_preserves_inputs_without_saving(operator: Client) -> None:
    fields = payload()
    fields["identifiers-0-identifier_type"] = "ISIN"
    response = operator.post(reverse("assets_assets_new"), fields)
    assert response.status_code == 422
    assert response.context["bundle"].main["name"].value() == "Example"
    assert not Asset.objects.exists()


def test_edit_and_delete_identifier_within_asset(operator: Client) -> None:
    fields = payload()
    fields.update(
        {
            "identifiers-0-identifier_type": "ISIN",
            "identifiers-0-value": "BEFORE",
        }
    )
    assert operator.post(reverse("assets_assets_new"), fields).status_code == 302
    asset = Asset.objects.get()
    identifier = asset.identifiers.get()
    fields.update(
        {
            "request_key": str(uuid.uuid4()),
            "identifiers-INITIAL_FORMS": "1",
            "identifiers-0-id": str(identifier.pk),
            "identifiers-0-value": "AFTER",
        }
    )
    url = reverse("assets_assets_edit", args=[asset.pk])
    assert operator.post(url, fields).status_code == 302
    identifier.refresh_from_db()
    assert identifier.value == "AFTER"
    fields.update({"request_key": str(uuid.uuid4()), "identifiers-0-DELETE": "on"})
    assert operator.post(url, fields).status_code == 302
    assert not asset.identifiers.exists()


def test_identifier_from_another_asset_cannot_be_modified(operator: Client) -> None:
    currency = currency_model().objects.get(code="USD")
    first = Asset.objects.create(
        name="First", short_name="F", currency=currency, asset_family="EQUITY", market_type="LISTED"
    )
    other = Asset.objects.create(
        name="Other", short_name="O", currency=currency, asset_family="EQUITY", market_type="LISTED"
    )
    identifier = AssetIdentifier.objects.create(asset=other, identifier_type="ISIN", value="OTHER")
    fields = payload()
    fields.update(
        {
            "identifiers-INITIAL_FORMS": "1",
            "identifiers-0-id": str(identifier.pk),
            "identifiers-0-identifier_type": "ISIN",
            "identifiers-0-value": "CHANGED",
        }
    )
    response = operator.post(reverse("assets_assets_edit", args=[first.pk]), fields)
    assert response.status_code == 422
    identifier.refresh_from_db()
    assert identifier.value == "OTHER"


def test_adding_identifier_requires_its_permission(operator: Client) -> None:
    user = User.objects.create_user("restricted")
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "add_asset",
                "view_assetidentifier",
            ]
        )
    )
    operator.force_login(user)
    fields = payload()
    fields.update({"identifiers-0-identifier_type": "ISIN", "identifiers-0-value": "TEST"})
    response = operator.post(reverse("assets_assets_new"), fields)
    assert response.status_code == 422
    assert not Asset.objects.exists()
