from typing import Any

import pytest
from django.test import Client

from maud.modules.products.models import Mandate
from maud.modules.products.responses import MandateResponse, ProductResponse

pytestmark = pytest.mark.django_db


def mandate_url(product: ProductResponse, mandate_id: Any, step: str = "") -> str:
    return f"/products/{product.id}/mandates/{mandate_id}/" + (f"?step={step}" if step else "")


def new_draft(admin_client: Client, product: ProductResponse) -> Mandate:
    admin_client.post(f"/products/{product.id}/mandates/start/")
    return Mandate.objects.get(state="DRAFT")


def test_new_version_copies_last_published(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    response = admin_client.post(f"/products/{product.id}/mandates/start/")

    draft = Mandate.objects.get(state="DRAFT")
    assert response["Location"] == mandate_url(product, draft.id)
    assert (draft.version, draft.risk_level) == (2, 2)


def test_profile_step_saves_and_marks_change_against_previous_version(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    draft = new_draft(admin_client, product)

    response = admin_client.post(
        mandate_url(product, draft.id, "profile"),
        {
            "risk_level": "4",
            "target_return_spread_pct": "2,5",
            "liquidity_days": "30",
            "max_average_term_years": "3,5",
            "eligible_asset_classes": ["EQUITY", "FIXED_INCOME"],
            "go": "next",
        },
    )
    page = admin_client.get(mandate_url(product, draft.id, "profile")).content.decode()

    draft.refresh_from_db()
    assert response["Location"] == mandate_url(product, draft.id, "flows")
    assert (draft.risk_level, str(draft.target_return_spread_pct)) == (4, "2.5000")
    assert "Na v1: <s>2 de 5</s>" in page


def test_text_that_is_not_a_number_shows_field_error(
    admin_client: Client, product: ProductResponse, draft: MandateResponse
) -> None:
    response = admin_client.post(
        mandate_url(product, draft.id, "flows"), {"min_initial_amount": "dez mil"}
    )

    assert response.status_code == 422
    assert "Use só números" in response.content.decode()


def test_limit_outside_eligible_classes_shows_error(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    draft = new_draft(admin_client, product)

    response = admin_client.post(
        mandate_url(product, draft.id, "limits"),
        {
            "limit_dimension": ["ASSET_CLASS"],
            "limit_target": ["REAL_ESTATE"],
            "limit_min": ["0"],
            "limit_max": ["10"],
        },
    )

    assert response.status_code == 422
    assert "não está entre as classes elegíveis" in response.content.decode()
    assert draft.exposure_limits.get().target == "EQUITY"  # o rascunho continua como estava


def test_limits_step_replaces_the_whole_list(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse, usd: Any
) -> None:
    draft = new_draft(admin_client, product)

    admin_client.post(
        mandate_url(product, draft.id, "limits"),
        {
            "limit_dimension": ["ASSET_CLASS", "CURRENCY"],
            "limit_target": ["EQUITY", "USD"],
            "limit_min": ["0", "80"],
            "limit_max": ["30", "100"],
        },
    )

    limits = {(row.target, str(row.max_pct)) for row in draft.exposure_limits.all()}
    assert limits == {("EQUITY", "30.00"), ("USD", "100.00")}


def test_published_mandate_is_read_only(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    url = mandate_url(product, published_mandate.id)

    page = admin_client.get(url).content.decode()
    admin_client.post(url, {"risk_level": "5"})

    assert "Versão publicada: não muda mais." in page
    assert 'name="risk_level"' not in page
    assert Mandate.objects.get(pk=published_mandate.id).risk_level == 2
