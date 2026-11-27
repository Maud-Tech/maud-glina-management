from typing import Any

import pytest
from django.test import Client

from maud.modules.products.models import Product

pytestmark = pytest.mark.django_db
URL = "/products/new/"


def test_new_product_starts_as_draft_in_usd(admin_client: Client, usd: Any) -> None:
    response = admin_client.post(
        URL, {"code": "GLINA-USD-09", "name": "Glina Teste", "base_currency": "USD"}
    )

    product = Product.objects.get()
    assert response.status_code == 302
    assert response["Location"] == f"/products/{product.id}/"
    assert (product.status, product.base_currency_id) == ("DRAFT", "USD")


def test_invalid_form_keeps_values_and_shows_field_errors(admin_client: Client, usd: Any) -> None:
    response = admin_client.post(
        URL,
        {
            "code": "GLINA-USD-09",
            "name": "Glina Teste",
            "base_currency": "USD",
            "launch_date": "2027-01-04",
            "closing_date": "2026-12-01",
        },
    )

    page = response.content.decode()
    assert response.status_code == 422
    assert "encerramento" in page.lower()
    assert 'value="GLINA-USD-09"' in page
    assert not Product.objects.exists()


def test_create_requires_add_permission(client: Client, django_user_model: Any) -> None:
    client.force_login(django_user_model.objects.create_user("consulta", password="x"))

    assert client.post(URL, {"code": "X", "name": "Y", "base_currency": "USD"}).status_code == 403
