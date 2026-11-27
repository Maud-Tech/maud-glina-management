"""Formulários e metadados dos cadastros do módulo; escrita só pelo handler."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from maud.modules.assets.models import (
    Asset,
    AssetClassification,
    AssetEvent,
    AssetIdentifier,
    AssetListing,
    AssetPrice,
    CashAsset,
    DebtInstrument,
    Equity,
    Fund,
    GenericAsset,
    PriceSource,
    TradingVenue,
)
from maud.modules.entities.api import reference_queryset

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
        if name == "DebtInstrument":
            if data.get("perpetual") and data.get("maturity_date"):
                self.add_error("maturity_date", "Dívida perpétua não possui vencimento.")
            if not data.get("perpetual") and not data.get("maturity_date"):
                self.add_error("maturity_date", "Informe o vencimento ou marque perpétuo.")
            if (
                data.get("issue_date")
                and data.get("maturity_date")
                and data["maturity_date"] <= data["issue_date"]
            ):
                self.add_error("maturity_date", "O vencimento deve ser posterior à emissão.")
        if name == "Fund":
            parent = data.get("parent_fund")
            visited = {self.instance.pk}
            while parent is not None:
                if parent.pk in visited:
                    self.add_error(
                        "parent_fund", "O vínculo de fundo pai não pode formar um ciclo."
                    )
                    break
                visited.add(parent.pk)
                parent = parent.parent_fund
        if name == "GenericAsset":
            data["raw_data"] = data.get("raw_data") or {}
            target = data.get("normalized_asset")
            if target and target.pk == self.instance.asset_id:
                self.add_error("normalized_asset", "Escolha outro ativo para normalização.")
        if (
            name == "AssetPrice"
            and data.get("price_type") == "CURVE"
            and data.get("asset")
            and data["asset"].asset_family != "DEBT"
        ):
            self.add_error("price_type", "Preço de curva é exclusivo de instrumentos de dívida.")
        if name == "AssetEvent" and (
            data.get("event_date")
            and data.get("settlement_date")
            and data["settlement_date"] < data["event_date"]
        ):
            self.add_error("settlement_date", "Liquidação não pode anteceder a Data COM.")
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
    form_type = forms.modelform_factory(
        model,
        form=RegistrationForm,
        exclude=excluded,
        labels=LABELS,
    )
    form = form_type(data=data, instance=instance, prefix=prefix)
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
    return form


@dataclass
class RegistrationForms:
    resource: str
    spec: RegistrationSpec
    main: Any
    detail: Any = None
    identity: str = "new"

    def is_valid(self) -> bool:
        main_valid = self.main.is_valid()
        detail_valid = self.detail.is_valid() if self.detail is not None else True
        if (
            self.detail is not None
            and self.spec.detail_parent == "asset"
            and self.detail._meta.model.__name__ == "CashAsset"
            and main_valid
        ):
            self.detail.instance.currency = self.main.cleaned_data["currency"]
        return main_valid and detail_valid

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
    return RegistrationForms(
        resource, spec, main, detail, str(instance.pk) if instance is not None else "new"
    )


REGISTRY = {
    "assets": RegistrationSpec(
        Asset,
        "Ativos",
        ("name", "asset_family", "currency", "status"),
        ("name", "short_name", "identifiers__value", "listings__ticker"),
        "asset_family",
        {
            "EQUITY": (Equity, "equity_details"),
            "DEBT": (DebtInstrument, "debt_details"),
            "FUND": (Fund, "fund_details"),
            "CASH": (CashAsset, "cash_details"),
            "GENERIC": (GenericAsset, "generic_details"),
        },
        "asset",
    ),
    "venues": RegistrationSpec(
        TradingVenue, "Casas de negociação", ("code", "name", "country"), ("code", "name")
    ),
    "sources": RegistrationSpec(
        PriceSource, "Fontes de preço", ("code", "name", "priority"), ("code", "name")
    ),
    "identifiers": RegistrationSpec(
        AssetIdentifier,
        "Identificadores",
        ("asset", "identifier_type", "value", "is_primary"),
        ("asset__name", "value"),
        parent_field="asset",
    ),
    "listings": RegistrationSpec(
        AssetListing,
        "Listagens",
        ("asset", "trading_venue", "ticker", "active"),
        ("asset__name", "ticker"),
        parent_field="asset",
    ),
    "classifications": RegistrationSpec(
        AssetClassification,
        "Classificações",
        ("asset", "asset_class", "liquidity_type"),
        ("asset__name", "asset_subclass"),
        parent_field="asset",
    ),
    "prices": RegistrationSpec(
        AssetPrice,
        "Preços",
        ("asset", "price_date", "price", "price_type", "source"),
        ("asset__name", "source__code"),
        parent_field="asset",
    ),
    "events": RegistrationSpec(
        AssetEvent,
        "Eventos de mercado",
        ("asset", "event_type", "event_date", "event_status"),
        ("asset__name",),
        parent_field="asset",
    ),
}


def configure_references(form: Any) -> None:
    for name, form_field in form.fields.items():
        if isinstance(form_field, forms.ModelChoiceField) and form_field.queryset is not None:
            target = form_field.queryset.model
            if target._meta.app_label == "entities":
                form_field.queryset = reference_queryset(target._meta.model_name)
                if target._meta.model_name == "entity":
                    form_field.queryset = form_field.queryset.filter(archived_at__isnull=True)
                    if name != "issuer_entity":
                        form_field.queryset = form_field.queryset.filter(entity_kind="COMPANY")
