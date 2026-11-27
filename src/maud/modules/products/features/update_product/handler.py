"""Alterar os dados do produto. Slice de COMANDO (tela, com login).

Passo a passo:
    1. valida e normaliza os dados (domain/product.py)
    2. trava o produto; encerrado não muda
    3. código e moeda-base só mudam no rascunho (e a moeda, só sem apólice)
    4. grava só se algo mudou, com a linha de histórico (antes e depois) na mesma transação

Status não muda aqui: é a slice change_product_status.
Erros: 404 product_not_found
       422 product_closed, product_code_locked, product_currency_locked,
           product_currency_has_policy, currency_not_found (+ os de create_product)
       409 product_code_taken
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.changes import changed_fields
from maud.modules.products.domain.product import (
    ProductStatus,
    check_editable,
    check_identity_change,
    validate_product,
)
from maud.modules.products.history import product_snapshot, record_product_change
from maud.modules.products.models import Product, ProductChange
from maud.modules.products.queries import check_currency_exists, get_product, product_policy
from maud.modules.products.responses import ProductResponse, product_response
from maud.shared.errors import ConflictError


@dataclass(frozen=True)
class UpdateProductCommand:
    actor_id: int
    product_id: UUID
    code: str
    name: str
    base_currency: str
    description: str = ""
    launch_date: date | None = None
    closing_date: date | None = None
    reason: str = ""


def execute(command: UpdateProductCommand) -> ProductResponse:
    # 1. Valida e normaliza
    data = validate_product(
        code=command.code,
        name=command.name,
        description=command.description,
        launch_date=command.launch_date,
        closing_date=command.closing_date,
    )
    currency = command.base_currency.strip().upper()

    with transaction.atomic():
        # 2. Trava; encerrado não muda
        product = get_product(command.product_id, for_update=True)
        status = ProductStatus(product.status)
        check_editable(status)

        # 3. Identidade
        code_changed = data.code != product.code
        currency_changed = currency != product.base_currency_id
        check_identity_change(
            status,
            code_changed=code_changed,
            currency_changed=currency_changed,
            has_policy=product_policy(product.id) is not None,
        )
        if currency_changed:
            check_currency_exists(currency)
        if code_changed and Product.objects.filter(code=data.code).exists():
            raise ConflictError(
                f"Já existe produto com o código {data.code}.", code="product_code_taken"
            )

        # 4. Grava só o que mudou
        before = product_snapshot(product)
        product.code = data.code
        product.name = data.name
        product.description = data.description
        product.base_currency_id = currency
        product.launch_date = data.launch_date
        product.closing_date = data.closing_date
        changes = changed_fields(before, product_snapshot(product))
        if changes:
            product.save()
            record_product_change(
                product_id=product.id,
                object_type=ProductChange.ObjectType.PRODUCT,
                object_id=product.id,
                action=ProductChange.Action.UPDATED,
                changes=changes,
                actor_id=command.actor_id,
                reason=command.reason,
            )

    return product_response(product)
