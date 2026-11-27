from typing import Any

import pytest
from django.test import Client

from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    execute as update_mandate_draft,
)
from maud.modules.products.models import Mandate, MandateChange
from maud.modules.products.responses import MandateResponse, ProductResponse
from maud.modules.products.testing import COMPLETE_TERMS, EQUITY_LIMIT

pytestmark = pytest.mark.django_db


def publish_url(product: ProductResponse, mandate_id: Any) -> str:
    return f"/products/{product.id}/mandates/{mandate_id}/publish/"


def test_first_version_is_published_and_goes_back_to_versions(
    admin_client: Client, actor: Any, product: ProductResponse, draft: MandateResponse
) -> None:
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id, mandate_id=draft.id, terms=COMPLETE_TERMS, limits=(EQUITY_LIMIT,)
        )
    )

    response = admin_client.post(publish_url(product, draft.id), {"effective_from": "2026-12-01"})

    assert response["Location"] == f"/products/{product.id}/?tab=mandate"
    assert Mandate.objects.get().state == "PUBLISHED"


def test_publish_requires_reason_from_second_version(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    admin_client.post(f"/products/{product.id}/mandates/start/")
    draft = Mandate.objects.get(state="DRAFT")

    response = admin_client.post(publish_url(product, draft.id), {"effective_from": "2026-12-20"})

    assert response.status_code == 422
    assert "Diga o motivo da versão nova" in response.content.decode()
    assert Mandate.objects.get(pk=draft.id).state == "DRAFT"

    admin_client.post(
        publish_url(product, draft.id), {"effective_from": "2026-12-20", "reason": "comitê"}
    )
    assert MandateChange.objects.get(action="PUBLISHED", mandate=draft).reason == "comitê"


def test_publish_page_shows_what_changes_and_warns_it_is_for_everyone(
    admin_client: Client, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    admin_client.post(f"/products/{product.id}/mandates/start/")
    draft = Mandate.objects.get(state="DRAFT")
    admin_client.post(
        f"/products/{product.id}/mandates/{draft.id}/?step=limits",
        {
            "limit_dimension": ["ASSET_CLASS"],
            "limit_target": ["EQUITY"],
            "limit_min": ["0"],
            "limit_max": ["30"],
        },
    )

    page = admin_client.get(publish_url(product, draft.id)).content.decode()

    assert "Limite Classe de ativo: Renda variável: 0% a 20% → 0% a 30%" in page
    assert "inclusive quem já comprou" in page
