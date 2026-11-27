"""Consultas usadas por várias slices do módulo. Dado de outro módulo, só pela fachada dele."""

from datetime import date
from uuid import UUID

from django.core.exceptions import ValidationError

from maud.modules.entities.api import reference_queryset
from maud.modules.products.domain.mandate import LimitDimension, LimitTerms, MandateState
from maud.modules.products.domain.policy import PolicyStatus, is_effective
from maud.modules.products.domain.product import ActivationReadiness
from maud.modules.products.models import Mandate, Policy, Product, ProductDocument
from maud.shared.errors import DomainError, NotFoundError

COMPANY_KIND = "COMPANY"  # Entity.Kind.COMPANY do módulo entities


def get_product(product_id: UUID, *, for_update: bool = False) -> Product:
    products = Product.objects.select_for_update() if for_update else Product.objects.all()
    try:
        return products.get(pk=product_id)
    except Product.DoesNotExist:
        raise NotFoundError("Produto não encontrado.", code="product_not_found") from None


def get_policy(policy_id: UUID, *, for_update: bool = False) -> Policy:
    policies = Policy.objects.select_for_update() if for_update else Policy.objects.all()
    try:
        return policies.get(pk=policy_id)
    except Policy.DoesNotExist:
        raise NotFoundError("Apólice não encontrada.", code="policy_not_found") from None


def get_mandate(mandate_id: UUID, *, for_update: bool = False) -> Mandate:
    mandates = Mandate.objects.select_for_update() if for_update else Mandate.objects.all()
    try:
        return mandates.get(pk=mandate_id)
    except Mandate.DoesNotExist:
        raise NotFoundError("Regulamento não encontrado.", code="mandate_not_found") from None


def get_document(document_id: UUID, *, for_update: bool = False) -> ProductDocument:
    documents = (
        ProductDocument.objects.select_for_update() if for_update else ProductDocument.objects.all()
    )
    try:
        return documents.get(pk=document_id)
    except ProductDocument.DoesNotExist:
        raise NotFoundError("Documento não encontrado.", code="document_not_found") from None


def product_policy(product_id: UUID) -> Policy | None:
    return Policy.objects.filter(product_id=product_id).first()


def latest_published_mandate(product_id: UUID) -> Mandate | None:
    return (
        Mandate.objects.filter(product_id=product_id, state=MandateState.PUBLISHED.value)
        .order_by("-version")
        .first()
    )


def current_mandate(product_id: UUID, on: date) -> Mandate | None:
    """Versão publicada que vale no dia `on` (a de vigência mais recente até esse dia)."""
    return (
        Mandate.objects.filter(
            product_id=product_id,
            state=MandateState.PUBLISHED.value,
            effective_from__lte=on,
        )
        .order_by("-effective_from")
        .first()
    )


def activation_readiness(product_id: UUID, on: date) -> ActivationReadiness:
    policy = product_policy(product_id)
    return ActivationReadiness(
        has_published_mandate=latest_published_mandate(product_id) is not None,
        has_effective_policy=policy is not None
        and is_effective(
            PolicyStatus(policy.status), policy.effective_from, policy.effective_until, on
        ),
    )


def check_currency_exists(code: str) -> None:
    if not reference_queryset("currency").filter(pk=code).exists():
        raise DomainError(f"Moeda {code} não está cadastrada.", code="currency_not_found")


def check_insurer(entity_id: UUID) -> None:
    """A seguradora é uma Entity jurídica (a regra do entities manda apontar para Entity)."""
    kind = (
        reference_queryset("entity")
        .filter(pk=entity_id)
        .values_list("entity_kind", flat=True)
        .first()
    )
    if kind is None:
        raise DomainError("Seguradora não encontrada.", code="insurer_not_found")
    if kind != COMPANY_KIND:
        raise DomainError(
            "A seguradora tem de ser pessoa jurídica.", code="insurer_must_be_company"
        )


_REFERENCE_BY_DIMENSION = {
    LimitDimension.COUNTRY: "country",
    LimitDimension.CURRENCY: "currency",
    LimitDimension.ISSUER: "entity",
}


def check_limit_targets(limits: tuple[LimitTerms, ...]) -> None:
    """País, moeda e emissor do limite têm de existir nos cadastros do entities."""
    for limit in limits:
        kind = _REFERENCE_BY_DIMENSION.get(limit.dimension)
        if kind is None:
            continue
        try:
            found = reference_queryset(kind).filter(pk=limit.target).exists()
        except (ValueError, ValidationError):  # emissor que não é um id válido
            found = False
        if not found:
            raise DomainError(
                f"Alvo do limite não encontrado: {limit.dimension.value} {limit.target}.",
                code="exposure_limit_target_not_found",
            )
