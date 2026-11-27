from typing import Any

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from maud.modules.products.models import Product, ProductChange
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db


def status_url(product: ProductResponse) -> str:
    return f"/products/{product.id}/status/"


def test_activation_goes_through_the_slice_and_records_reason(
    admin_client: Client, product: ProductResponse, policy: Any, published_mandate: Any
) -> None:
    response = admin_client.post(status_url(product), {"status": "ACTIVE", "reason": "lançamento"})

    assert response.status_code == 302
    assert response["Location"] == f"/products/{product.id}/"
    assert Product.objects.get().status == "ACTIVE"
    assert ProductChange.objects.get(action="STATUS_CHANGED").reason == "lançamento"


def test_refused_activation_returns_with_the_rule_message(
    admin_client: Client, product: ProductResponse
) -> None:
    response = admin_client.post(status_url(product), {"status": "ACTIVE"}, follow=True)

    assert Product.objects.get().status == "DRAFT"
    assert "notice error" in response.content.decode()


def test_status_change_requires_change_permission(
    client: Client, django_user_model: Any, product: ProductResponse
) -> None:
    user = django_user_model.objects.create_user("consulta", password="x")
    user.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.force_login(user)

    assert client.post(status_url(product), {"status": "CLOSED"}).status_code == 403
    assert Product.objects.get().status == "DRAFT"


def test_status_change_only_accepts_post(admin_client: Client, product: ProductResponse) -> None:
    assert admin_client.get(status_url(product)).status_code == 405
