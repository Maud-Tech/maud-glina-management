"""Fixtures dos testes do módulo products: relógio fixo, quem opera, cadastros e produto pronto."""

from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from django.apps import apps

from maud.modules.products.features.create_product.handler import (
    CreateProductCommand,
)
from maud.modules.products.features.create_product.handler import (
    execute as create_product,
)
from maud.modules.products.features.publish_mandate.handler import (
    PublishMandateCommand,
)
from maud.modules.products.features.publish_mandate.handler import (
    execute as publish_mandate,
)
from maud.modules.products.features.register_policy.handler import (
    RegisterPolicyCommand,
)
from maud.modules.products.features.register_policy.handler import (
    execute as register_policy,
)
from maud.modules.products.features.start_mandate_draft.handler import (
    StartMandateDraftCommand,
)
from maud.modules.products.features.start_mandate_draft.handler import (
    execute as start_mandate_draft,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    execute as update_mandate_draft,
)
from maud.modules.products.responses import MandateResponse, PolicyResponse, ProductResponse
from maud.modules.products.testing import COMPLETE_TERMS, EQUITY_LIMIT, NOW, TODAY
from maud.shared.clock import FixedClock, use_clock


@pytest.fixture(autouse=True)
def clock() -> Iterator[FixedClock]:
    with use_clock(FixedClock(NOW)) as fixed:
        assert isinstance(fixed, FixedClock)
        yield fixed


@pytest.fixture
def actor(db: None, django_user_model: Any) -> Any:
    return django_user_model.objects.create_user("operadora")


@pytest.fixture
def usd(db: None) -> Any:
    return apps.get_model("entities", "Currency").objects.create(
        code="USD", name="US Dollar", symbol="US$"
    )


@pytest.fixture
def eur(db: None) -> Any:
    return apps.get_model("entities", "Currency").objects.create(
        code="EUR", name="Euro", symbol="€"
    )


@pytest.fixture
def united_states(usd: Any) -> Any:
    return apps.get_model("entities", "Country").objects.create(
        code="US", name="United States", currency=usd
    )


@pytest.fixture
def insurer(db: None) -> Any:
    return apps.get_model("entities", "Entity").objects.create(
        entity_kind="COMPANY", display_name="Seguradora Exemplo"
    )


@pytest.fixture
def other_insurer(db: None) -> Any:
    return apps.get_model("entities", "Entity").objects.create(
        entity_kind="COMPANY", display_name="Outra Seguradora"
    )


@pytest.fixture
def person(db: None) -> Any:
    return apps.get_model("entities", "Entity").objects.create(
        entity_kind="PERSON", display_name="Pessoa Exemplo"
    )


@pytest.fixture
def product(actor: Any, usd: Any) -> ProductResponse:
    return create_product(
        CreateProductCommand(actor_id=actor.id, code="GLINA-USD-01", name="Glina USD Conservador")
    )


@pytest.fixture
def policy(actor: Any, product: ProductResponse, insurer: Any) -> PolicyResponse:
    return register_policy(
        RegisterPolicyCommand(
            actor_id=actor.id,
            product_id=product.id,
            policy_number="AP-0001",
            insurer_entity_id=insurer.id,
            effective_from=TODAY - timedelta(days=30),
            effective_until=TODAY + timedelta(days=365),
        )
    )


@pytest.fixture
def draft(actor: Any, product: ProductResponse) -> MandateResponse:
    return start_mandate_draft(StartMandateDraftCommand(actor_id=actor.id, product_id=product.id))


@pytest.fixture
def published_mandate(actor: Any, draft: MandateResponse) -> MandateResponse:
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor.id, mandate_id=draft.id, terms=COMPLETE_TERMS, limits=(EQUITY_LIMIT,)
        )
    )
    return publish_mandate(
        PublishMandateCommand(actor_id=actor.id, mandate_id=draft.id, effective_from=TODAY)
    )
