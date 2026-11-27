from pathlib import Path
from typing import Any

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from maud.modules.products.features.attach_product_document.handler import (
    MAX_DOCUMENT_BYTES,
    AttachProductDocumentCommand,
    execute,
)
from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.models import ProductChange, ProductDocument
from maud.modules.products.responses import PolicyResponse, ProductResponse
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db

PDF_BYTES = b"%PDF-1.7\n%fake but signed\n"


@pytest.fixture(autouse=True)
def media_in_tmp(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


def pdf(content: bytes = PDF_BYTES, name: str = "regulamento.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content)


def attach(actor: Any, product: ProductResponse, **changes: Any) -> Any:
    fields: dict[str, Any] = {
        "actor_id": actor.id,
        "product_id": product.id,
        "document_type": "MANDATE",
        "title": " Regulamento   v1 ",
        "file": pdf(),
    }
    fields.update(changes)
    return execute(AttachProductDocumentCommand(**fields))


def test_pdf_is_stored_with_new_name_and_recorded(actor: Any, product: ProductResponse) -> None:
    document = attach(actor, product)

    stored = ProductDocument.objects.get()
    assert document.title == "Regulamento v1"
    assert document.content_type == "application/pdf"
    assert document.size_bytes == len(PDF_BYTES)
    assert str(stored.file.name).startswith("products/")
    assert str(stored.file.name).endswith(".pdf")
    assert "regulamento" not in str(stored.file.name)
    assert default_storage.exists(str(stored.file.name))
    change = ProductChange.objects.get(object_type="DOCUMENT")
    assert change.action == "CREATED"
    assert change.object_id == document.id


def test_document_may_point_to_the_product_policy(
    actor: Any, product: ProductResponse, policy: PolicyResponse
) -> None:
    document = attach(actor, product, document_type="POLICY_CONTRACT", policy_id=policy.id)

    assert document.policy_id == policy.id


def test_policy_of_another_product_is_rejected(actor: Any, policy: PolicyResponse) -> None:
    other = create_product(CreateProductCommand(actor_id=actor.id, code="P2", name="Outro"))

    with pytest.raises(DomainError) as error:
        attach(actor, other, policy_id=policy.id)

    assert error.value.code == "document_policy_mismatch"


def test_file_that_is_not_a_pdf_is_rejected(actor: Any, product: ProductResponse) -> None:
    with pytest.raises(DomainError) as error:
        attach(actor, product, file=pdf(b"PK\x03\x04 planilha", name="regulamento.pdf"))

    assert error.value.code == "document_format_not_allowed"
    assert not ProductDocument.objects.exists()


def test_file_over_size_limit_is_rejected(actor: Any, product: ProductResponse) -> None:
    too_big = pdf(PDF_BYTES + b"x" * MAX_DOCUMENT_BYTES)

    with pytest.raises(DomainError) as error:
        attach(actor, product, file=too_big)

    assert error.value.code == "document_too_large"


def test_unknown_document_type_is_rejected(actor: Any, product: ProductResponse) -> None:
    with pytest.raises(DomainError) as error:
        attach(actor, product, document_type="SPREADSHEET")

    assert error.value.code == "document_type_unknown"
