from typing import Any
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db
TABS = ("overview", "mandate", "policy", "documents", "history")


def detail(product: ProductResponse, tab: str = "") -> str:
    return f"/products/{product.id}/" + (f"?tab={tab}" if tab else "")


def test_every_tab_opens(
    admin_client: Client, product: ProductResponse, policy: Any, published_mandate: Any
) -> None:
    for tab in TABS:
        assert admin_client.get(detail(product, tab)).status_code == 200


def test_unknown_product_is_404(admin_client: Client) -> None:
    assert admin_client.get(f"/products/{uuid4()}/").status_code == 404


def test_activation_shows_what_is_missing(admin_client: Client, product: ProductResponse) -> None:
    page = admin_client.get(detail(product)).content.decode()

    assert "Ainda não dá para ativar" in page
    assert "uma apólice ativa e vigente hoje e o regulamento publicado" in page


def test_ready_product_offers_activation_confirmation(
    admin_client: Client, product: ProductResponse, policy: Any, published_mandate: Any
) -> None:
    page = admin_client.get(detail(product)).content.decode()

    assert "Ativar o produto?" in page
    assert "Ainda não dá para ativar" not in page


def test_overview_shows_mandate_in_force(
    admin_client: Client, product: ProductResponse, published_mandate: Any
) -> None:
    page = admin_client.get(detail(product)).content.decode()

    assert "SOFR + 2,00% a.a." in page
    assert "Classe de ativo: Renda variável" in page
    assert "0% a 20%" in page


def test_history_shows_before_after_author_and_reason(
    admin_client: Client, product: ProductResponse
) -> None:
    admin_client.post(f"/products/{product.id}/status/", {"status": "CLOSED", "reason": "fim"})

    page = admin_client.get(detail(product, "history")).content.decode()

    assert "Status alterado" in page
    assert "<s>Rascunho</s> → <b>Encerrado</b>" in page
    assert "admin" in page
    assert "fim" in page


def test_viewer_sees_no_write_buttons(
    client: Client, django_user_model: Any, product: ProductResponse
) -> None:
    user = django_user_model.objects.create_user("consulta", password="x")
    user.user_permissions.add(Permission.objects.get(codename="view_product"))
    client.force_login(user)

    page = client.get(detail(product)).content.decode()

    assert "/edit/" not in page
    assert 'data-dialog="status-' not in page
