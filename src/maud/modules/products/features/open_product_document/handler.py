"""Abrir o PDF de um documento do produto. Slice de CONSULTA (só lê, tela com login).

Arquivo enviado não é público (ADR 0010): só a tela, com login e permissão, entrega o conteúdo.
Documento arquivado continua abrindo (fica no histórico).
Erros: 404 document_not_found (inclusive documento de outro produto)
"""

from dataclasses import dataclass
from uuid import UUID

from django.core.files import File

from maud.modules.products.queries import get_document
from maud.shared.errors import NotFoundError


@dataclass(frozen=True)
class OpenProductDocumentQuery:
    product_id: UUID
    document_id: UUID


@dataclass(frozen=True)
class DocumentFile:
    title: str
    content_type: str
    content: "File[bytes]"  # genérico só para o mypy; o File do Django não é subscritível


def execute(query: OpenProductDocumentQuery) -> DocumentFile:
    document = get_document(query.document_id)
    if document.product_id != query.product_id:
        raise NotFoundError("Documento não encontrado.", code="document_not_found")
    document.file.open("rb")
    return DocumentFile(
        title=document.title, content_type=document.content_type, content=document.file
    )
