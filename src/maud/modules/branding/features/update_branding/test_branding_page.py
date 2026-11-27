from typing import Any

import pytest
from django.test import Client

from maud.modules.branding.models import Branding

pytestmark = pytest.mark.django_db
URL = "/settings/branding/"


def test_anonymous_user_is_sent_to_login(client: Client) -> None:
    response = client.get(URL)

    assert response.status_code == 302
    assert response["Location"].startswith("/login/")


def test_user_without_permission_is_refused_with_403(
    client: Client, django_user_model: Any
) -> None:
    client.force_login(django_user_model.objects.create_user("operadora", password="x"))

    assert client.get(URL).status_code == 403


def test_admin_saves_and_returns_to_the_page(admin_client: Client) -> None:
    response = admin_client.post(URL, {"name": "Gestora Exemplo", "brand_color": "#3B82F6"})

    assert response.status_code == 302
    assert response["Location"] == URL
    assert Branding.objects.get().brand_color == "#3B82F6"


def test_unreadable_color_shows_the_error_in_the_field(admin_client: Client) -> None:
    response = admin_client.post(URL, {"name": "Gestora Exemplo", "brand_color": "#787878"})

    assert response.status_code == 422
    assert "texto do botão fica ilegível" in response.content.decode()
    assert not Branding.objects.exists()
