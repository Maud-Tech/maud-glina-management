from pathlib import Path
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.models import ProductDocument
from maud.modules.products.responses import ProductResponse

pytestmark = pytest.mark.django_db
PDF = b"%PDF-1.7\n%fake but signed\n"


@pytest.fixture(autouse=True)
def media_in_tmp(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


def upload(client: Client, product: ProductResponse, content: bytes = PDF) -> Any:
    return client.post(
        f"/products/{product.id}/documents/",
        {
            "document_type": "MANDATE",
            "title": "Regulamento v1",
            "file": SimpleUploadedFile("regulamento.pdf", content),
        },
    )


def test_pdf_upload_is_listed_and_opens_with_login(
    admin_client: Client, client: Client, product: ProductResponse
) -> None:
    response = upload(admin_client, product)
    document = ProductDocument.objects.get()
    page = admin_client.get(f"/products/{product.id}/?tab=documents").content.decode()
    opened = admin_client.get(f"/products/{product.id}/documents/{document.id}/")
    anonymous = client.get(f"/products/{product.id}/documents/{document.id}/")

    assert response["Location"] == f"/products/{product.id}/?tab=documents"
    assert "Regulamento v1" in page
    assert opened["Content-Type"] == "application/pdf"
    assert b"".join(opened.streaming_content) == PDF  # type: ignore[attr-defined]
    assert anonymous.status_code == 302


def test_file_that_is_not_pdf_is_refused(admin_client: Client, product: ProductResponse) -> None:
    response = upload(admin_client, product, b"PK\x03\x04 planilha")

    assert "notice error" in admin_client.get(response["Location"]).content.decode()
    assert not ProductDocument.objects.exists()


def test_archived_document_stays_listed_as_archived(
    admin_client: Client, product: ProductResponse
) -> None:
    upload(admin_client, product)
    document = ProductDocument.objects.get()

    admin_client.post(
        f"/products/{product.id}/documents/{document.id}/archive/", {"reason": "nova versão"}
    )
    page = admin_client.get(f"/products/{product.id}/?tab=documents").content.decode()

    assert ProductDocument.objects.get().archived_at is not None
    assert "file archived" in page
    assert "arquivado em" in page


def test_document_of_another_product_is_404(
    admin_client: Client, actor: Any, product: ProductResponse
) -> None:
    upload(admin_client, product)
    document = ProductDocument.objects.get()
    other = create_product(CreateProductCommand(actor_id=actor.id, code="P2", name="Outro"))

    assert admin_client.get(f"/products/{other.id}/documents/{document.id}/").status_code == 404
