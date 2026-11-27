from typing import Any

import pytest
from django.test import Client

from maud.modules.products.models import Policy
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db


def test_policy_is_registered_with_a_company_insurer(
    admin_client: Client, product: ProductResponse, insurer: Any, person: Any
) -> None:
    form = admin_client.get(f"/products/{product.id}/policy/new/").content.decode()
    response = admin_client.post(
        f"/products/{product.id}/policy/new/",
        {
            "policy_number": "AP-0009",
            "insurer_entity_id": str(insurer.id),
            "effective_from": "2026-11-01",
        },
    )

    assert "Seguradora Exemplo" in form
    assert "Pessoa Exemplo" not in form
    assert response["Location"] == f"/products/{product.id}/?tab=policy"
    assert Policy.objects.get().currency_id == "USD"


def test_policy_dates_error_shows_in_the_end_field(
    admin_client: Client, product: ProductResponse, insurer: Any
) -> None:
    response = admin_client.post(
        f"/products/{product.id}/policy/new/",
        {
            "policy_number": "AP-0009",
            "insurer_entity_id": str(insurer.id),
            "effective_from": "2026-11-01",
            "effective_until": "2026-10-01",
        },
    )

    assert response.status_code == 422
    assert 'value="AP-0009"' in response.content.decode()
    assert not Policy.objects.exists()


def test_expired_policy_cannot_be_edited(
    admin_client: Client, product: ProductResponse, policy: Any
) -> None:
    admin_client.post(f"/products/{product.id}/policy/expire/")

    response = admin_client.get(f"/products/{product.id}/policy/edit/")

    assert response.status_code == 302
    assert response["Location"] == f"/products/{product.id}/?tab=policy"
