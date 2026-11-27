"""Aceitação: ciclo de vida do produto, da apólice e do regulamento (task de cadastro de produtos).

Regras combinadas com o time em 27/11/2026:
- produto só fica ativo com regulamento publicado e apólice ativa e vigente;
- versão nova do regulamento vale para todos, inclusive quem já comprou, a partir da vigência,
  e a versão anterior continua gravada;
- expirar a apólice expira o produto, que depois só pode ser encerrado;
- toda alteração fica no histórico, com quem fez e o motivo.
"""

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.apps import apps

from maud.modules.products.domain.mandate import LimitDimension, LimitTerms, MandateTerms
from maud.modules.products.features.change_product_status.handler import (
    ChangeProductStatusCommand,
)
from maud.modules.products.features.change_product_status.handler import (
    execute as change_status,
)
from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.features.expire_policy.handler import ExpirePolicyCommand
from maud.modules.products.features.expire_policy.handler import execute as expire_policy
from maud.modules.products.features.get_product.handler import GetProductQuery
from maud.modules.products.features.get_product.handler import execute as get_product
from maud.modules.products.features.list_product_history.handler import ListProductHistoryQuery
from maud.modules.products.features.list_product_history.handler import (
    execute as list_history,
)
from maud.modules.products.features.publish_mandate.handler import PublishMandateCommand
from maud.modules.products.features.publish_mandate.handler import execute as publish_mandate
from maud.modules.products.features.register_policy.handler import RegisterPolicyCommand
from maud.modules.products.features.register_policy.handler import execute as register_policy
from maud.modules.products.features.start_mandate_draft.handler import StartMandateDraftCommand
from maud.modules.products.features.start_mandate_draft.handler import (
    execute as start_mandate_draft,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
)
from maud.modules.products.features.update_mandate_draft.handler import (
    execute as update_mandate_draft,
)
from maud.shared.clock import FixedClock, use_clock
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db

START = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
TERMS = MandateTerms(
    risk_level=2,
    target_return_spread_pct=Decimal("2"),
    liquidity_days=30,
    max_average_term_years=Decimal("3"),
    eligible_asset_classes=("EQUITY", "FIXED_INCOME"),
    min_initial_amount=Decimal("10000"),
    subscription_settlement_days=2,
    redemption_settlement_days=5,
)
EQUITY_UP_TO_20 = LimitTerms(LimitDimension.ASSET_CLASS, "EQUITY", Decimal("0"), Decimal("20"))


@pytest.fixture
def clock() -> Iterator[FixedClock]:
    with use_clock(FixedClock(START)) as fixed:
        assert isinstance(fixed, FixedClock)
        yield fixed


@pytest.fixture
def operator(django_user_model: Any) -> Any:
    return django_user_model.objects.create_user("operadora")


@pytest.fixture
def insurer() -> Any:
    apps.get_model("entities", "Currency").objects.create(code="USD", name="US Dollar", symbol="$")
    return apps.get_model("entities", "Entity").objects.create(
        entity_kind="COMPANY", display_name="Seguradora"
    )


def test_product_goes_live_changes_rules_for_everyone_and_expires_with_its_policy(
    clock: FixedClock, operator: Any, insurer: Any
) -> None:
    today = START.date()
    actor = operator.id

    # Produto em rascunho, em USD
    product = create_product(CreateProductCommand(actor_id=actor, code="GLINA-01", name="Glina"))
    assert (product.status, product.base_currency) == ("DRAFT", "USD")

    # Sem regulamento publicado e sem apólice, não ativa
    with pytest.raises(DomainError):
        change_status(
            ChangeProductStatusCommand(actor_id=actor, product_id=product.id, status="ACTIVE")
        )

    # Apólice com seguradora jurídica + regulamento v1 publicado hoje
    policy = register_policy(
        RegisterPolicyCommand(
            actor_id=actor,
            product_id=product.id,
            policy_number="AP-1",
            insurer_entity_id=insurer.id,
            effective_from=today,
        )
    )
    v1 = start_mandate_draft(StartMandateDraftCommand(actor_id=actor, product_id=product.id))
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor, mandate_id=v1.id, terms=TERMS, limits=(EQUITY_UP_TO_20,)
        )
    )
    publish_mandate(PublishMandateCommand(actor_id=actor, mandate_id=v1.id, effective_from=today))

    # Agora ativa
    active = change_status(
        ChangeProductStatusCommand(actor_id=actor, product_id=product.id, status="ACTIVE")
    )
    assert active.status == "ACTIVE"

    # v2: renda variável até 30%, vale para todos a partir de 01/01; v1 continua gravada
    clock.advance(timedelta(days=10))
    v2 = start_mandate_draft(StartMandateDraftCommand(actor_id=actor, product_id=product.id))
    update_mandate_draft(
        UpdateMandateDraftCommand(
            actor_id=actor,
            mandate_id=v2.id,
            terms=TERMS,
            limits=(replace(EQUITY_UP_TO_20, max_pct=Decimal("30")),),
        )
    )
    publish_mandate(
        PublishMandateCommand(
            actor_id=actor,
            mandate_id=v2.id,
            effective_from=today + timedelta(days=31),
            reason="decisão do comitê",
        )
    )
    detail = get_product(GetProductQuery(product_id=product.id))
    assert detail.current_mandate is not None and detail.current_mandate.version == 1
    assert detail.upcoming_mandate is not None and detail.upcoming_mandate.version == 2

    clock.advance(timedelta(days=21))  # passou de 01/01: a v2 vale para todos
    detail = get_product(GetProductQuery(product_id=product.id))
    assert detail.current_mandate is not None and detail.current_mandate.version == 2
    assert detail.current_mandate.exposure_limits[0].max_pct == Decimal("30")

    # Apólice expira: produto expira junto e só pode ser encerrado
    expire_policy(
        ExpirePolicyCommand(actor_id=actor, policy_id=policy.id, reason="fim do contrato")
    )
    assert get_product(GetProductQuery(product_id=product.id)).product.status == "EXPIRED"
    with pytest.raises(DomainError):
        change_status(
            ChangeProductStatusCommand(actor_id=actor, product_id=product.id, status="ACTIVE")
        )
    closed = change_status(
        ChangeProductStatusCommand(actor_id=actor, product_id=product.id, status="CLOSED")
    )
    assert closed.status == "CLOSED"

    # Tudo no histórico, com autor; o motivo da v2 está lá
    history = list_history(ListProductHistoryQuery(product_id=product.id))
    assert all(entry.changed_by == "operadora" for entry in history)
    assert any(
        entry.action == "PUBLISHED" and entry.reason == "decisão do comitê" for entry in history
    )
