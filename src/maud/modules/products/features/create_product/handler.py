"""Cadastrar produto. Slice de COMANDO (tela, com login).

Passo a passo:
    1. valida e normaliza os dados (domain/product.py)
    2. confere a moeda-base no cadastro de moedas (entities)
    3. recusa código repetido
    4. grava o produto em rascunho e a linha de histórico, na mesma transação

Não é idempotente por chave: o código único barra o cadastro repetido.
Sem evento: este app não avisa ninguém (ADR 0008); o leitor lê pela API de leitura.
Erros: 422 product_code_invalid, product_name_required, product_name_too_long,
           product_dates_invalid, currency_not_found
       409 product_code_taken
"""

from dataclasses import dataclass
from datetime import date

from django.db import transaction

from maud.modules.products.domain.product import (
    DEFAULT_BASE_CURRENCY,
    ProductStatus,
    validate_product,
)
from maud.modules.products.history import as_created, product_snapshot, record_product_change
from maud.modules.products.models import Product, ProductChange
from maud.modules.products.queries import check_currency_exists
from maud.modules.products.responses import ProductResponse, product_response
from maud.shared.errors import ConflictError


@dataclass(frozen=True)
class CreateProductCommand:
    actor_id: int
    code: str
    name: str
    description: str = ""
    base_currency: str = DEFAULT_BASE_CURRENCY
    launch_date: date | None = None
    closing_date: date | None = None


def execute(command: CreateProductCommand) -> ProductResponse:
    # 1. Valida e normaliza
    data = validate_product(
        code=command.code,
        name=command.name,
        description=command.description,
        launch_date=command.launch_date,
        closing_date=command.closing_date,
    )
    currency = command.base_currency.strip().upper() or DEFAULT_BASE_CURRENCY

    # 2. Moeda-base cadastrada
    check_currency_exists(currency)

    with transaction.atomic():
        # 3. Código único (o banco também garante)
        if Product.objects.filter(code=data.code).exists():
            raise ConflictError(
                f"Já existe produto com o código {data.code}.", code="product_code_taken"
            )

        # 4. Grava em rascunho + histórico
        product = Product.objects.create(
            code=data.code,
            name=data.name,
            description=data.description,
            base_currency_id=currency,
            status=ProductStatus.DRAFT.value,
            launch_date=data.launch_date,
            closing_date=data.closing_date,
        )
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.PRODUCT,
            object_id=product.id,
            action=ProductChange.Action.CREATED,
            changes=as_created(product_snapshot(product)),
            actor_id=command.actor_id,
        )

    return product_response(product)
