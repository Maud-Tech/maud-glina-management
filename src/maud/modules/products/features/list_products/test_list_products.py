from typing import Any

import pytest

from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.features.list_products.handler import ListProductsQuery, execute
from maud.modules.products.responses import MandateResponse, ProductResponse

pytestmark = pytest.mark.django_db


def test_lists_products_with_current_mandate_version_and_risk(
    actor: Any, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    create_product(CreateProductCommand(actor_id=actor.id, code="AAA-01", name="Sem regulamento"))

    rows = execute(ListProductsQuery())

    assert [row.code for row in rows] == ["AAA-01", "GLINA-USD-01"]
    assert (rows[0].mandate_version, rows[0].risk_level) == (None, None)
    assert (rows[1].mandate_version, rows[1].risk_level) == (1, 2)


def test_filters_by_code_or_name_and_by_status(actor: Any, product: ProductResponse) -> None:
    create_product(CreateProductCommand(actor_id=actor.id, code="OUTRO", name="Outro produto"))

    assert [row.code for row in execute(ListProductsQuery(search="conservador"))] == [
        "GLINA-USD-01"
    ]
    assert [row.code for row in execute(ListProductsQuery(search="outr"))] == ["OUTRO"]
    assert execute(ListProductsQuery(status="ACTIVE")) == []
