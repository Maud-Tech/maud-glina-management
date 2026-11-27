from typing import Any

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def save_branding(
    admin_client: Client, name: str = "Gestora Exemplo", color: str = "#8B5CF6"
) -> None:
    response = admin_client.post("/settings/branding/", {"name": name, "brand_color": color})
    assert response.status_code == 302


def test_dashboard_requires_login(client: Client) -> None:
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"].startswith("/login/")


def test_login_page_shows_the_gestora_name(client: Client, admin_client: Client) -> None:
    save_branding(admin_client, name="Atlântica Gestão")

    assert "Atlântica Gestão" in client.get("/login/").content.decode()


def test_brand_color_reaches_every_page(admin_client: Client) -> None:
    save_branding(admin_client, color="#8B5CF6")

    page = admin_client.get("/").content.decode()

    assert "--brand: #8B5CF6" in page
    assert "--on-brand: #FFFFFF" in page


def test_theme_cookie_chooses_the_light_theme(admin_client: Client) -> None:
    admin_client.cookies["theme"] = "light"

    assert 'data-theme="light"' in admin_client.get("/").content.decode()


def test_unknown_theme_falls_back_to_dark(admin_client: Client) -> None:
    admin_client.cookies["theme"] = "neon"

    assert 'data-theme="dark"' in admin_client.get("/").content.decode()


def test_menu_hides_personalization_from_user_without_permission(
    client: Client, django_user_model: Any
) -> None:
    client.force_login(django_user_model.objects.create_user("operadora", password="x"))

    page = client.get("/").content.decode()

    assert 'href="/settings/branding/"' not in page
    assert "Só administrador" in page
