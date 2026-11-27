from typing import Any

import pytest
from django.test import Client

from maud.modules.products.models import Policy, Product
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db


def test_expire_policy_expires_product_and_only_close_remains(
    admin_client: Client, product: ProductResponse, policy: Any, published_mandate: Any
) -> None:
    admin_client.post(f"/products/{product.id}/status/", {"status": "ACTIVE"})

    response = admin_client.post(
        f"/products/{product.id}/policy/expire/", {"reason": "não renovou"}
    )
    page = admin_client.get(f"/products/{product.id}/").content.decode()

    assert response["Location"] == f"/products/{product.id}/?tab=policy"
    assert Policy.objects.get().status == "EXPIRED"
    assert Product.objects.get().status == "EXPIRED"
    assert 'data-dialog="status-closed"' in page
    assert 'data-dialog="status-active"' not in page
    assert 'data-dialog="status-inactive"' not in page


def test_policy_tab_asks_confirmation_before_expiring(
    admin_client: Client, product: ProductResponse, policy: Any
) -> None:
    page = admin_client.get(f"/products/{product.id}/?tab=policy").content.decode()

    assert 'data-dialog="expire-policy"' in page
    assert "Expirar a apólice AP-0001?" in page
