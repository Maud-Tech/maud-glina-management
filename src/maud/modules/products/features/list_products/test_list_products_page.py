from typing import Any

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db
URL = "/products/"


def viewer(client: Client, django_user_model: Any) -> Any:
    user = django_user_model.objects.create_user("consulta", password="x")
    user.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.force_login(user)
    return user


def test_product_pages_require_login(client: Client, product: ProductResponse) -> None:
    for url in (URL, reverse("products_detail", args=[product.id]), "/products/new/"):
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith("/login/")


def test_user_without_view_permission_is_refused(client: Client, django_user_model: Any) -> None:
    client.force_login(django_user_model.objects.create_user("sem-acesso", password="x"))

    assert client.get(URL).status_code == 403


def test_viewer_sees_list_without_new_button_and_menu_item(
    client: Client, django_user_model: Any, product: ProductResponse
) -> None:
    viewer(client, django_user_model)

    page = client.get(URL).content.decode()

    assert "GLINA-USD-01" in page
    assert 'href="/products/new/"' not in page
    assert "Cadastro de produtos" in page


def test_product_list_filters_by_status_and_search(
    admin_client: Client, actor: Any, product: ProductResponse
) -> None:
    create_product(CreateProductCommand(actor_id=actor.id, code="OUTRO-01", name="Outro"))

    by_search = admin_client.get(URL, {"q": "outro"}).content.decode()
    by_status = admin_client.get(URL, {"status": "ACTIVE"}).content.decode()

    assert "OUTRO-01" in by_search and "GLINA-USD-01" not in by_search
    assert "Nenhum produto encontrado" in by_status


def test_list_shows_policy_and_mandate_in_force(
    admin_client: Client, policy: Any, published_mandate: Any
) -> None:
    page = admin_client.get(URL).content.decode()

    assert "v1 · risco 2" in page
    assert "AP-0001" in page
