from pathlib import Path
from typing import Any

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from maud.modules.products.features.archive_product_document.handler import (
    ArchiveProductDocumentCommand,
    execute,
)
from maud.modules.products.features.attach_product_document.handler import (
    AttachProductDocumentCommand,
)
from maud.modules.products.features.attach_product_document.handler import (
    execute as attach_document,
)
from maud.modules.products.models import ProductChange, ProductDocument
from maud.modules.products.responses import DocumentResponse, ProductResponse
from maud.modules.products.testing import NOW
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


@pytest.fixture
def document(
    settings: Any, tmp_path: Path, actor: Any, product: ProductResponse
) -> DocumentResponse:
    settings.MEDIA_ROOT = tmp_path
    return attach_document(
        AttachProductDocumentCommand(
            actor_id=actor.id,
            product_id=product.id,
            document_type="FACT_SHEET",
            title="Lâmina",
            file=SimpleUploadedFile("lamina.pdf", b"%PDF-1.7\n"),
        )
    )


def test_archived_document_keeps_file_and_records_reason(
    actor: Any, document: DocumentResponse
) -> None:
    archived = execute(
        ArchiveProductDocumentCommand(
            actor_id=actor.id, document_id=document.id, reason="lâmina nova"
        )
    )

    assert archived.archived_at == NOW
    stored = ProductDocument.objects.get()
    assert default_storage.exists(str(stored.file.name))
    change = ProductChange.objects.get(object_type="DOCUMENT", action="ARCHIVED")
    assert change.reason == "lâmina nova"


def test_archiving_twice_is_rejected(actor: Any, document: DocumentResponse) -> None:
    execute(ArchiveProductDocumentCommand(actor_id=actor.id, document_id=document.id))

    with pytest.raises(DomainError) as error:
        execute(ArchiveProductDocumentCommand(actor_id=actor.id, document_id=document.id))

    assert error.value.code == "document_already_archived"
