"""Telas do módulo products (ADR 0010): uma linha por tela ou ação; o config/urls.py inclui."""

from django.urls import path

from maud.modules.products.features.archive_product_document.page import document_archive
from maud.modules.products.features.attach_product_document.page import document_attach
from maud.modules.products.features.change_product_status.page import product_status
from maud.modules.products.features.create_product.page import product_new
from maud.modules.products.features.expire_policy.page import policy_expire
from maud.modules.products.features.get_product.page import product_detail
from maud.modules.products.features.list_products.page import product_list
from maud.modules.products.features.open_product_document.page import document_open
from maud.modules.products.features.publish_mandate.page import mandate_publish
from maud.modules.products.features.register_policy.page import policy_new
from maud.modules.products.features.start_mandate_draft.page import mandate_start
from maud.modules.products.features.update_mandate_draft.page import mandate_page
from maud.modules.products.features.update_policy.page import policy_edit
from maud.modules.products.features.update_product.page import product_edit

PRODUCT = "products/<uuid:product_id>/"

urlpatterns = [
    path("products/", product_list, name="products_list"),
    path("products/new/", product_new, name="products_new"),
    path(PRODUCT, product_detail, name="products_detail"),
    path(PRODUCT + "edit/", product_edit, name="products_edit"),
    path(PRODUCT + "status/", product_status, name="products_status"),
    path(PRODUCT + "policy/new/", policy_new, name="products_policy_new"),
    path(PRODUCT + "policy/edit/", policy_edit, name="products_policy_edit"),
    path(PRODUCT + "policy/expire/", policy_expire, name="products_policy_expire"),
    path(PRODUCT + "mandates/start/", mandate_start, name="products_mandate_start"),
    path(PRODUCT + "mandates/<uuid:mandate_id>/", mandate_page, name="products_mandate"),
    path(
        PRODUCT + "mandates/<uuid:mandate_id>/publish/",
        mandate_publish,
        name="products_mandate_publish",
    ),
    path(PRODUCT + "documents/", document_attach, name="products_document_attach"),
    path(
        PRODUCT + "documents/<uuid:document_id>/",
        document_open,
        name="products_document_open",
    ),
    path(
        PRODUCT + "documents/<uuid:document_id>/archive/",
        document_archive,
        name="products_document_archive",
    ),
]
