"""Preços sem fontes: tipos, unicidade e telas."""

import uuid
from typing import Any

import pytest
from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from maud.modules.assets.models import Asset, AssetPrice

pytestmark = pytest.mark.django_db


@pytest.fixture
def operator(client: Client) -> Client:
    user = User.objects.create_superuser("operator", password="test-only")
    client.force_login(user)
    return client


@pytest.fixture
def debt() -> Asset:
    currency_model: Any = apps.get_model("entities", "Currency")
    currency = currency_model.objects.create(code="USD", name="US Dollar", symbol="$")
    return Asset.objects.create(
        name="Debt",
        short_name="D",
        currency=currency,
        asset_family="DEBT",
        market_type="OTC",
    )


def price_data(asset: Asset, price_type: str = "MKT") -> dict[str, str]:
    return {
        "request_key": str(uuid.uuid4()),
        "main-asset": str(asset.pk),
        "main-price_date": "2026-11-27",
        "main-price": "100.123456789012",
        "main-currency": "USD",
        "main-price_type": price_type,
    }


def test_price_form_and_menu_have_no_source(operator: Client) -> None:
    response = operator.get(reverse("assets_prices_new"))
    assert response.status_code == 200
    assert "source" not in response.context["bundle"].main.fields
    assert "Fontes de preço" not in response.content.decode()
    assert operator.get("/assets/sources/").status_code == 404
    assert "PriceSource" not in {
        model.__name__ for model in apps.get_app_config("assets").get_models()
    }


def test_price_types_can_coexist_without_sources(operator: Client, debt: Asset) -> None:
    assert set(AssetPrice.Type.values) == {"MKT", "MD", "CURVE"}
    for kind in AssetPrice.Type.values:
        response = operator.post(reverse("assets_prices_new"), price_data(debt, kind))
        assert response.status_code == 302
    assert AssetPrice.objects.filter(asset=debt, price_date="2026-11-27").count() == 3


def test_price_rejects_duplicate_asset_date_type(operator: Client, debt: Asset) -> None:
    url = reverse("assets_prices_new")
    assert operator.post(url, price_data(debt)).status_code == 302
    duplicate = operator.post(url, price_data(debt))
    assert duplicate.status_code == 422
    assert AssetPrice.objects.count() == 1


def test_price_replay_does_not_duplicate(operator: Client, debt: Asset) -> None:
    fields = price_data(debt, "MD")
    url = reverse("assets_prices_new")
    assert operator.post(url, fields).status_code == 302
    assert operator.post(url, fields).status_code == 302
    assert AssetPrice.objects.count() == 1


@pytest.mark.parametrize("invalid", ["OTHER", "SOURCE", ""])
def test_price_type_must_be_one_of_three(operator: Client, debt: Asset, invalid: str) -> None:
    assert operator.post(reverse("assets_prices_new"), price_data(debt, invalid)).status_code == 422
    assert not AssetPrice.objects.exists()
