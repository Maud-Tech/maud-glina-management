"""Anexar um documento ao produto (regulamento, lâmina, contrato da apólice). Slice de COMANDO.

Passo a passo:
    1. valida título e tipo; confere o arquivo pelo conteúdo (só PDF) e o tamanho
    2. trava o produto; encerrado não muda; a apólice informada tem de ser deste produto
    3. guarda o arquivo no storage padrão (nome novo, imprevisível) e grava o documento
    4. linha de histórico (DOCUMENT, CREATED) na mesma transação

Vem da tela, com login; abrir o arquivo também exige login (ui.md, seção 7).
Erros: 404 product_not_found
       422 document_title_required, document_type_unknown, document_too_large,
           document_format_not_allowed, document_policy_mismatch, product_closed
"""

from __future__ import annotations  # UploadedFile[bytes] só existe para o mypy

from dataclasses import dataclass
from uuid import UUID

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from maud.modules.products.domain.product import ProductStatus, check_editable, normalize_text
from maud.modules.products.history import as_created, document_snapshot, record_product_change
from maud.modules.products.models import Policy, ProductChange, ProductDocument
from maud.modules.products.queries import get_product
from maud.modules.products.responses import DocumentResponse, document_response
from maud.shared.clock import get_clock
from maud.shared.errors import DomainError

MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
PDF_CONTENT_TYPE = "application/pdf"


@dataclass(frozen=True)
class AttachProductDocumentCommand:
    actor_id: int
    product_id: UUID
    document_type: str
    title: str
    file: UploadedFile[bytes]
    policy_id: UUID | None = None


def execute(command: AttachProductDocumentCommand) -> DocumentResponse:
    # 1. Título, tipo e arquivo
    title = normalize_text(command.title)
    if not title:
        raise DomainError("Dê um título ao documento.", code="document_title_required")
    if command.document_type not in ProductDocument.Type.values:
        raise DomainError(
            f"Tipo de documento desconhecido: {command.document_type}.",
            code="document_type_unknown",
        )
    size = _checked_pdf_size(command.file)

    with transaction.atomic():
        # 2. Produto e apólice
        product = get_product(command.product_id, for_update=True)
        check_editable(ProductStatus(product.status))
        if (
            command.policy_id is not None
            and not Policy.objects.filter(pk=command.policy_id, product=product).exists()
        ):
            raise DomainError(
                "A apólice informada não é deste produto.", code="document_policy_mismatch"
            )

        # 3. Arquivo no storage + registro
        document = ProductDocument(
            product=product,
            policy_id=command.policy_id,
            document_type=command.document_type,
            title=title,
            content_type=PDF_CONTENT_TYPE,
            size_bytes=size,
            uploaded_by_id=command.actor_id,
            uploaded_at=get_clock().now(),
        )
        document.file.save("document.pdf", command.file, save=False)
        document.save()

        # 4. Histórico
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.DOCUMENT,
            object_id=document.id,
            action=ProductChange.Action.CREATED,
            changes=as_created(document_snapshot(document)),
            actor_id=command.actor_id,
        )

    return document_response(document)


def _checked_pdf_size(upload: UploadedFile[bytes]) -> int:
    """Confere tamanho e formato pelo conteúdo (assinatura do PDF), não pelo nome."""
    size = upload.size or 0
    if size > MAX_DOCUMENT_BYTES:
        raise DomainError("O arquivo passa de 20 MB.", code="document_too_large")
    try:
        header = upload.read(len(PDF_SIGNATURE))
    finally:
        upload.seek(0)
    if header != PDF_SIGNATURE:
        raise DomainError("Envie o documento em PDF.", code="document_format_not_allowed")
    return size
