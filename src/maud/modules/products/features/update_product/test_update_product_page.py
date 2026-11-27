from typing import Any

import pytest
from django.test import Client

from maud.modules.products.models import Product, ProductChange
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db


def edit_url(product: ProductResponse) -> str:
    return f"/products/{product.id}/edit/"


def test_draft_product_edit_saves_with_reason(
    admin_client: Client, product: ProductResponse
) -> None:
    response = admin_client.post(
        edit_url(product),
        {
            "code": "GLINA-USD-01",
            "name": "Glina Novo Nome",
            "base_currency": "USD",
            "reason": "nome comercial",
        },
    )

    assert response.status_code == 302
    assert Product.objects.get().name == "Glina Novo Nome"
    assert ProductChange.objects.get(action="UPDATED").reason == "nome comercial"


def test_code_and_currency_are_locked_after_draft(
    admin_client: Client, product: ProductResponse, policy: Any, published_mandate: Any
) -> None:
    admin_client.post(f"/products/{product.id}/status/", {"status": "ACTIVE"})

    page = admin_client.get(edit_url(product)).content.decode()
    admin_client.post(
        edit_url(product),
        {"code": "OUTRO-CODIGO", "name": "Glina", "base_currency": "USD"},
    )

    assert 'name="code"' in page and "disabled" in page.split('name="code"')[1].split(">")[0]
    assert Product.objects.get().code == "GLINA-USD-01"
