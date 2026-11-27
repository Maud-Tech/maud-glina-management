"""Arquivar um documento do produto. Slice de COMANDO (tela, com login).

Documento nunca é apagado: arquivar tira da lista de vigentes e o arquivo continua guardado.

Passo a passo:
    1. trava produto e documento (nessa ordem); produto encerrado não muda
    2. documento já arquivado é recusado
    3. grava a data e a linha de histórico (DOCUMENT, ARCHIVED) na mesma transação

Erros: 404 document_not_found
       422 product_closed, document_already_archived
"""

from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import record_product_change
from maud.modules.products.models import ProductChange
from maud.modules.products.queries import get_document, get_product
from maud.modules.products.responses import DocumentResponse, document_response
from maud.shared.clock import get_clock
from maud.shared.errors import DomainError


@dataclass(frozen=True)
class ArchiveProductDocumentCommand:
    actor_id: int
    document_id: UUID
    reason: str = ""


def execute(command: ArchiveProductDocumentCommand) -> DocumentResponse:
    with transaction.atomic():
        # 1. Trava produto e documento
        product_id = get_document(command.document_id).product_id
        product = get_product(product_id, for_update=True)
        document = get_document(command.document_id, for_update=True)
        check_editable(ProductStatus(product.status))

        # 2. Já arquivado
        if document.archived_at is not None:
            raise DomainError("O documento já está arquivado.", code="document_already_archived")

        # 3. Arquiva + histórico
        document.archived_at = get_clock().now()
        document.save(update_fields=["archived_at"])
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.DOCUMENT,
            object_id=document.id,
            action=ProductChange.Action.ARCHIVED,
            changes={"archived_at": [None, document.archived_at]},
            actor_id=command.actor_id,
            reason=command.reason,
        )

    return document_response(document)
