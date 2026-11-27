"""Formulários e metadados dos cadastros do módulo; escrita só pelo handler."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any, cast

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.forms.models import BaseModelFormSet

from maud.modules.entities.models import (
    Country,
    Currency,
    Entity,
    EntityAddress,
    EntityCompany,
    EntityContact,
    EntityPerson,
)

LABELS = {
    "code": "Código",
    "name": "Nome",
    "symbol": "Símbolo",
    "decimal_places": "Casas decimais",
    "active": "Ativo",
    "currency": "Moeda",
    "entity_kind": "Natureza",
    "display_name": "Nome de exibição",
    "registration_country": "País de registro",
    "registration_number": "Número de registro",
    "notes": "Observações",
    "full_name": "Nome completo",
    "birth_date": "Data de nascimento",
    "birth_country": "País de nascimento",
    "residence_country": "País de residência",
    "nationality_country": "Nacionalidade",
    "legal_name": "Razão social",
    "trading_name": "Nome fantasia",
    "incorporation_country": "País de constituição",
    "sector": "Setor",
    "entity": "Pessoa",
    "address_type": "Tipo de endereço",
    "address_line_1": "Endereço",
    "address_line_2": "Complemento",
    "address_line_3": "Complemento adicional",
    "locality": "Cidade",
    "administrative_area": "Estado / província",
    "postal_code": "Código postal",
    "country": "País",
    "formatted_address": "Endereço formatado",
    "is_primary": "Principal",
    "contact_type": "Tipo de contato",
    "value": "Valor",
    "asset_family": "Família",
    "short_name": "Nome curto",
    "issuer_entity": "Emissor",
    "country_of_risk": "País de risco",
    "market_type": "Mercado",
    "description": "Descrição",
    "status": "Situação",
    "metadata": "Dados complementares (JSON)",
    "asset": "Ativo",
    "trading_venue": "Casa de negociação",
    "ticker": "Ticker",
    "identifier_type": "Tipo de identificador",
    "equity_type": "Tipo de renda variável",
    "instrument_type": "Instrumento",
    "debt_type": "Tipo de dívida",
    "guarantor_entity": "Garantidor",
    "insurer_entity": "Seguradora",
    "issue_date": "Data de emissão",
    "maturity_date": "Vencimento",
    "minimum_lot": "Lote mínimo",
    "coupon_type": "Tipo de cupom",
    "coupon_rate": "Taxa do cupom (%)",
    "reference_rate": "Indexador",
    "seniority": "Senioridade",
    "secured": "Com garantia",
    "perpetual": "Perpétuo",
    "callable": "Resgatável pelo emissor",
    "putable": "Resgatável pelo investidor",
    "convertible": "Conversível",
    "fund_type": "Tipo de fundo",
    "fund_name": "Nome do fundo",
    "share_class": "Classe de cotas",
    "parent_fund": "Fundo pai",
    "domicile_country": "País de domicílio",
    "manager_entity": "Gestor",
    "administrator_entity": "Administrador",
    "custodian_entity": "Custodiante",
    "legal_structure": "Estrutura jurídica",
    "open_ended": "Fundo aberto",
    "nav_frequency": "Frequência do valor da cota",
    "subscription_settlement_days": "Liquidação da aplicação (dias)",
    "redemption_notice_days": "Aviso de resgate (dias)",
    "redemption_settlement_days": "Liquidação do resgate (dias)",
    "management_fee_pct": "Taxa de gestão (%)",
    "performance_fee_pct": "Taxa de performance (%)",
    "high_water_mark": "Marca d'água",
    "benchmark_asset": "Ativo de referência",
    "distribution_policy": "Política de distribuição",
    "generic_type": "Tipo genérico",
    "raw_data": "Dados originais (JSON)",
    "normalization_status": "Situação da normalização",
    "normalization_notes": "Observações da normalização",
    "normalized_asset": "Ativo normalizado",
    "asset_class": "Classe",
    "asset_subclass": "Subclasse",
    "region": "Região",
    "liquidity_type": "Tipo de liquidez",
    "liquidity_days": "Liquidez (dias)",
    "classification_source": "Origem da classificação",
    "risk_factors": "Fatores de risco (JSON)",
    "priority": "Prioridade",
    "price_date": "Data do preço",
    "price": "Preço",
    "price_type": "Tipo de preço",
    "source": "Fonte de preço",
    "event_type": "Tipo de evento",
    "event_date": "Data COM",
    "settlement_date": "Data de liquidação",
    "percentage_rate": "Taxa percentual",
    "amount_paid": "Valor pago",
    "cum_price": "Preço COM",
    "factor": "Fator",
    "event_status": "Situação do evento",
}

COMPANY_SECTORS = (
    ("rental", "Aluguel"),
    ("consumer_staples", "Bens de Consumo"),
    ("consumer_discretionary", "Consumo Discricionário"),
    ("energy", "Energia"),
    ("financials", "Financeiro"),
    ("real_estate", "Imóveis"),
    ("industrials", "Industriais"),
    ("materials", "Materiais"),
    ("health_care", "Saúde"),
    ("communication_services", "Serviços de Comunicação"),
    ("utilities", "Serviços Públicos"),
    ("information_technology", "Tecnologia da Informação"),
)


@dataclass(frozen=True)
class RegistrationSpec:
    model: Any
    title: str
    columns: tuple[str, ...]
    search: tuple[str, ...]
    variant_field: str = ""
    variants: Any = field(default_factory=dict)
    detail_parent: str = ""
    parent_field: str = ""


class RegistrationForm(forms.ModelForm):  # type: ignore[type-arg]
    """Validações de cadastro além das constraints declaradas no model."""

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        model = self._meta.model
        if model is None:
            return data
        name = model.__name__
        for field_name, form_field in self.fields.items():
            if isinstance(form_field, forms.JSONField):
                data[field_name] = data.get(field_name) or {}
        if name == "Entity":
            country, number = data.get("registration_country"), data.get("registration_number")
            if bool(country) != bool(number):
                self.add_error("registration_number", "Informe país e número de registro juntos.")
            if data.get("entity_kind") == "COMPANY" and not country:
                self.add_error("registration_country", "Pessoa jurídica exige país e registro.")
        if name == "EntityContact" and data.get("value"):
            try:
                if data.get("contact_type") == "EMAIL":
                    validate_email(data["value"])
            except ValidationError:
                self.add_error("value", "Informe um e-mail válido.")
        return data


def build_form(
    model: Any,
    *,
    data: Any = None,
    instance: Any = None,
    prefix: str = "main",
    exclude: Any = (),
) -> Any:
    excluded = ["created_at", "updated_at", "archived_at", *exclude]
    if model is Currency:
        excluded.append("decimal_places")
    form_type = forms.modelform_factory(
        model,
        form=RegistrationForm,
        exclude=excluded,
        labels=LABELS,
    )
    form = form_type(data=data, instance=instance, prefix=prefix)
    if model is EntityCompany:
        form.fields["sector"] = forms.ChoiceField(
            label="Setor", required=False, choices=(("", "Selecione (opcional)"), *COMPANY_SECTORS)
        )
    style_form(form, model, instance)
    return form


def style_form(form: Any, model: Any, instance: Any = None) -> None:
    for name, form_field in form.fields.items():
        form_field.widget.attrs["class"] = "in"
        if isinstance(form_field, forms.DateField):
            form_field.widget = forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date", "class": "in"}
            )
        if isinstance(form_field, forms.JSONField):
            form_field.widget.attrs["rows"] = 4
            form_field.required = not model._meta.get_field(name).blank
            form_field.help_text = 'Informe um objeto JSON válido, por exemplo: {"nota": "texto"}.'
        if isinstance(form_field.widget, forms.Textarea):
            form_field.widget.attrs["rows"] = 3
        if instance is not None and name == model._meta.pk.name:
            form_field.disabled = True
        if name in {"registration_number", "value"} and isinstance(form_field, forms.CharField):
            form_field.strip = False
    configure_references(form)


class RelatedRegistrationFormSet(BaseModelFormSet):  # type: ignore[type-arg]
    """Itens vazios são opcionais; tipos primários não podem se repetir."""

    registration_can_add: bool = False

    def add_fields(self, form: Any, index: Any) -> None:
        super().add_fields(form, index)
        style_form(form, self.model)
        if "DELETE" in form.fields:
            form.fields["DELETE"].label = "Remover este item"

    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return
        primary_types: set[str] = set()
        type_field = "address_type" if self.model is EntityAddress else "contact_type"
        for form in self.forms:
            values = form.cleaned_data
            if not values or values.get("DELETE") or not values.get("is_primary"):
                continue
            kind = values.get(type_field, "")
            if kind in primary_types:
                form.add_error("is_primary", "Já existe um item principal deste tipo.")
            primary_types.add(kind)


def related_formsets(*, data: Any, instance: Any, permissions: Any) -> list[tuple[str, Any]]:
    result = []
    for prefix, model, title in (
        ("addresses", EntityAddress, "Endereços (opcional)"),
        ("contacts", EntityContact, "Contatos (opcional)"),
    ):
        rights = permissions.get(prefix, {})
        if not (rights.get("view") or rights.get("add") or rights.get("change")):
            continue
        factory = forms.modelformset_factory(
            model,
            form=RegistrationForm,
            formset=RelatedRegistrationFormSet,
            exclude=("entity", "created_at", "updated_at"),
            labels=LABELS,
            extra=1 if rights.get("add") else 0,
            can_delete=bool(rights.get("delete")),
            max_num=100,
            validate_max=True,
        )
        records = model.objects.filter(entity=instance) if instance else model.objects.none()
        bound_data = data
        # Clientes antigos sem a seção inline não alteram os vínculos existentes.
        if data is not None and prefix + "-TOTAL_FORMS" not in data:
            if any(name.startswith(prefix + "-") for name in data):
                bound_data = data  # management form inválido: mostrar erro, não ignorar dados.
            else:
                continue
        formset = cast(
            RelatedRegistrationFormSet, factory(data=bound_data, queryset=records, prefix=prefix)
        )
        for item in formset.forms:
            style_form(item, model)
            id_field = item.fields["id"]
            if isinstance(id_field, forms.ModelChoiceField):
                id_field.queryset = records
            if not item.instance._state.adding and not rights.get("change"):
                for name, form_field in item.fields.items():
                    if name not in {"id", "DELETE"}:
                        form_field.disabled = True
        style_form(formset.empty_form, model)
        formset.registration_can_add = bool(rights.get("add"))
        result.append((title, formset))
    return result


@dataclass
class RegistrationForms:
    resource: str
    spec: RegistrationSpec
    main: Any
    detail: Any = None
    identity: str = "new"
    related: Any = field(default_factory=list)
    related_permissions: Any = field(default_factory=dict)

    def is_valid(self) -> bool:
        main_valid = self.main.is_valid()
        detail_valid = self.detail.is_valid() if self.detail is not None else True
        related_valid = True
        for _, formset in self.related:
            valid = formset.is_valid()
            rights = self.related_permissions.get(formset.prefix, {})
            for item in formset.forms:
                if item.has_changed() and item.instance._state.adding and not rights.get("add"):
                    item.add_error(None, "Você não tem permissão para adicionar este item.")
                    valid = False
            related_valid = related_valid and valid
        return main_valid and detail_valid and related_valid

    def add_detail_errors(self, error: ValidationError) -> None:
        for name, errors in getattr(error, "message_dict", {"__all__": error.messages}).items():
            for message in errors:
                self.detail.add_error(name if name in self.detail.fields else None, message)


def registration_forms(
    resource: str,
    *,
    data: Any = None,
    instance: Any = None,
    variant: str = "",
    related_permissions: Any = None,
) -> RegistrationForms:
    spec = REGISTRY[resource]
    main = build_form(spec.model, data=data, instance=instance)
    detail = None
    if spec.variant_field:
        chosen = getattr(instance, spec.variant_field) if instance else variant
        if chosen not in spec.variants:
            chosen = next(iter(spec.variants))
        main.fields[spec.variant_field].initial = chosen
        main.fields[spec.variant_field].disabled = True
        detail_model, relation = spec.variants[chosen]
        detail_instance = None
        if instance is not None:
            with contextlib.suppress(ObjectDoesNotExist):
                detail_instance = getattr(instance, relation)
        excluded = [spec.detail_parent]
        if detail_model.__name__ == "CashAsset":
            excluded.append("currency")
        detail = build_form(
            detail_model, data=data, instance=detail_instance, prefix="detail", exclude=excluded
        )
        if instance is not None:
            setattr(detail.instance, spec.detail_parent, instance)
    bundle = RegistrationForms(
        resource, spec, main, detail, str(instance.pk) if instance is not None else "new"
    )
    if resource == "people" and related_permissions is not None:
        bundle.related_permissions = related_permissions
        bundle.related = related_formsets(
            data=data, instance=instance, permissions=related_permissions
        )
    return bundle


REGISTRY = {
    "currencies": RegistrationSpec(
        Currency, "Moedas", ("code", "name", "symbol"), ("code", "name")
    ),
    "countries": RegistrationSpec(
        Country, "Países", ("code", "name", "currency"), ("code", "name")
    ),
    "people": RegistrationSpec(
        Entity,
        "Pessoas físicas e jurídicas",
        ("display_name", "entity_kind", "registration_country", "registration_number"),
        ("display_name", "registration_number"),
        "entity_kind",
        {"PERSON": (EntityPerson, "person_details"), "COMPANY": (EntityCompany, "company_details")},
        "entity",
    ),
    "addresses": RegistrationSpec(
        EntityAddress,
        "Endereços",
        ("entity", "address_type", "locality", "country"),
        ("entity__display_name", "address_line_1", "locality"),
        parent_field="entity",
    ),
    "contacts": RegistrationSpec(
        EntityContact,
        "Contatos",
        ("entity", "contact_type", "value", "is_primary"),
        ("entity__display_name", "value"),
        parent_field="entity",
    ),
}


def configure_references(form: Any) -> None:
    pass
