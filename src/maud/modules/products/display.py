"""Apoio às telas do módulo: rótulos, formatação brasileira e opções dos campos de escolha.

Só leitura. Nada aqui grava; a tela grava pelo handler da slice.
"""

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from django.utils import timezone

from maud.modules.assets.api import asset_class_choices
from maud.modules.entities.api import reference_queryset
from maud.modules.products.domain.mandate import REQUIRED_TO_PUBLISH, LimitDimension
from maud.modules.products.models import (
    ExposureLimit,
    Mandate,
    MandateChange,
    Policy,
    Product,
    ProductChange,
    ProductDocument,
)
from maud.modules.products.queries import COMPANY_KIND

PRODUCT_STATUS = dict(Product.Status.choices)
POLICY_STATUS = dict(Policy.Status.choices)
MANDATE_STATE = dict(Mandate.State.choices)
DOCUMENT_TYPES = dict(ProductDocument.Type.choices)
DIMENSIONS = dict(ExposureLimit.Dimension.choices)
OBJECT_TYPES = {
    **dict(ProductChange.ObjectType.choices),
    "MANDATE": "Regulamento",
    "EXPOSURE_LIMIT": "Limite",
}
ACTIONS = {**dict(ProductChange.Action.choices), **dict(MandateChange.Action.choices)}

# Rótulo de cada campo que aparece no histórico e nas conferências
FIELD_LABELS = {
    "code": "código",
    "name": "nome",
    "description": "descrição",
    "base_currency": "moeda base",
    "status": "status",
    "launch_date": "lançamento",
    "closing_date": "encerramento",
    "policy_number": "número",
    "insurer_entity": "seguradora",
    "currency": "moeda",
    "issue_date": "emissão",
    "effective_from": "vigência",
    "effective_until": "fim da vigência",
    "document_type": "tipo",
    "title": "título",
    "policy": "apólice",
    "content_type": "formato",
    "size_bytes": "tamanho",
    "state": "estado",
    "risk_level": "nível de risco",
    "target_return_benchmark": "referência do retorno-alvo",
    "target_return_spread_pct": "spread do retorno-alvo",
    "liquidity_days": "liquidez",
    "max_average_term_years": "prazo médio máximo",
    "eligible_asset_classes": "classes elegíveis",
    "min_initial_amount": "aplicação inicial mínima",
    "min_additional_amount": "aplicação adicional mínima",
    "subscription_settlement_days": "liquidação da aplicação",
    "min_redemption_amount": "resgate mínimo",
    "min_balance_amount": "saldo mínimo",
    "redemption_notice_days": "aviso de resgate",
    "redemption_settlement_days": "liquidação do resgate",
    "lock_up_months": "carência",
    "notes": "observações",
    "dimension": "dimensão",
    "target": "alvo",
    "min_pct": "mínimo",
    "max_pct": "máximo",
}
# Valores codificados que viram texto no histórico
VALUE_LABELS = {
    **PRODUCT_STATUS,
    **POLICY_STATUS,
    **MANDATE_STATE,
    **DOCUMENT_TYPES,
    **DIMENSIONS,
}
EMPTY = "—"


def asset_class_labels() -> dict[str, str]:
    return dict(asset_class_choices())


def missing_to_publish(terms: Any) -> list[str]:
    """Rótulos do que ainda falta para publicar (mesma lista da regra `check_publishable`)."""
    missing = [FIELD_LABELS[name] for name in REQUIRED_TO_PUBLISH if getattr(terms, name) is None]
    if not terms.eligible_asset_classes:
        missing.append(FIELD_LABELS["eligible_asset_classes"])
    return missing


# ---------- formatação ----------


def number(value: Decimal | int | None, places: int = 2) -> str:
    """1234.5 → "1.234,50" (padrão brasileiro)."""
    if value is None:
        return EMPTY
    text = f"{Decimal(value):,.{places}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def trimmed(value: Decimal | None) -> str:
    """Decimal sem zeros sobrando à direita: 3.50 → "3,5"; 2.0000 → "2"."""
    if value is None:
        return ""
    text = format(value.normalize(), "f")
    return text.replace(".", ",")


def money(currency: str, value: Decimal | None) -> str:
    return EMPTY if value is None else f"{currency} {number(value)}"


def day(value: date | datetime | None) -> str:
    if value is None:
        return EMPTY
    if isinstance(value, datetime):
        value = timezone.localtime(value).date()
    return value.strftime("%d/%m/%Y")


def moment(value: datetime) -> tuple[str, str]:
    local = timezone.localtime(value)
    return local.strftime("%d/%m/%Y"), local.strftime("%H:%M")


def size(value: int) -> str:
    if value < 1024:
        return f"{value} bytes"
    if value < 1024 * 1024:
        return f"{number(Decimal(value) / 1024, 1)} KB"
    return f"{number(Decimal(value) / (1024 * 1024), 1)} MB"


def history_value(field: str, value: Any, names: dict[str, str]) -> str:
    """Um valor gravado no histórico (JSON) como texto da tela."""
    if value is None or value == "" or value == []:
        return EMPTY
    if isinstance(value, list):
        classes = asset_class_labels()
        return ", ".join(classes.get(str(item), str(item)) for item in value)
    text = str(value)
    if field in {"insurer_entity", "target", "policy"} and text in names:
        return names[text]
    if field == "size_bytes" and isinstance(value, int):
        return size(value)
    if field == "content_type":
        return "PDF" if text == "application/pdf" else text
    if field == "target":
        return asset_class_labels().get(text, text)
    if text in VALUE_LABELS:
        return VALUE_LABELS[text]
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text[8:10]}/{text[5:7]}/{text[0:4]}"
    return text


# ---------- entrada ----------


def parse_decimal(raw: str) -> Decimal | None:
    """Aceita "2,50", "2.50" e "10.000,00". Vazio vira None. Inválido levanta ValueError."""
    text = raw.strip().replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(raw) from None


def parse_int(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    return int(text)


# ---------- opções dos campos de escolha ----------


def currency_options() -> list[tuple[str, str]]:
    return [
        (row["code"], f"{row['code']} · {row['name']}")
        for row in reference_queryset("currency").filter(active=True).values("code", "name")
    ]


def insurer_options() -> list[tuple[str, str]]:
    companies = (
        reference_queryset("entity")
        .filter(entity_kind=COMPANY_KIND, archived_at__isnull=True)
        .order_by("display_name")
        .values("id", "display_name")
    )
    return [(str(row["id"]), row["display_name"]) for row in companies]


def entity_names(ids: Iterable[str]) -> dict[str, str]:
    """Nome de cada entidade pelo id. O que não é id (ex.: alvo "USD" de um limite) é ignorado."""
    wanted = []
    for value in ids:
        try:
            wanted.append(UUID(str(value)))
        except ValueError:
            continue
    if not wanted:
        return {}
    rows = reference_queryset("entity").filter(pk__in=wanted).values("id", "display_name")
    return {str(row["id"]): row["display_name"] for row in rows}


def limit_target_options() -> dict[str, list[tuple[str, str]]]:
    """Alvos possíveis de cada dimensão. Ativo único não tem alvo (vale para qualquer ativo)."""
    return {
        LimitDimension.ASSET_CLASS.value: list(asset_class_choices()),
        LimitDimension.CURRENCY.value: currency_options(),
        LimitDimension.COUNTRY.value: [
            (row["code"], f"{row['code']} · {row['name']}")
            for row in reference_queryset("country").values("code", "name")
        ],
        LimitDimension.ISSUER.value: [
            (str(row["id"]), row["display_name"])
            for row in reference_queryset("entity")
            .filter(archived_at__isnull=True)
            .order_by("display_name")
            .values("id", "display_name")
        ],
        LimitDimension.SINGLE_ASSET.value: [],
    }


def limit_target_label(
    dimension: str, target: str, options: dict[str, list[tuple[str, str]]]
) -> str:
    if not target:
        return "Qualquer ativo"
    return dict(options.get(dimension, [])).get(target, target)


# ---------- termos do regulamento em texto ----------


def percent(value: Decimal | None) -> str:
    """Spread e limites: 2 casas, ou até 4 quando houver (2.1250 → "2,125")."""
    if value is None:
        return EMPTY
    places = 2 if value == round(value, 2) else 4
    return number(value, places).rstrip("0") if places == 4 else number(value, 2)


def _count(value: int | None, unit: str) -> str:
    return EMPTY if value is None else f"{value} {unit}"


def _settlement(value: int | None) -> str:
    return EMPTY if value is None else f"D+{value}"


def term_text(name: str, terms: Any, currency: str) -> str:
    """Um termo do regulamento como texto da tela (`terms`: MandateResponse ou MandateTerms)."""
    value = getattr(terms, name)
    if name == "risk_level":
        return EMPTY if value is None else f"{value} de 5"
    if name == "target_return_spread_pct":
        return EMPTY if value is None else f"SOFR + {percent(value)}% a.a."
    if name == "liquidity_days":
        return _count(value, "dias")
    if name == "max_average_term_years":
        return EMPTY if value is None else f"{trimmed(value)} anos"
    if name == "eligible_asset_classes":
        labels = asset_class_labels()
        return ", ".join(labels.get(code, code) for code in value) or EMPTY
    if name in {"subscription_settlement_days", "redemption_settlement_days"}:
        return _settlement(value)
    if name == "redemption_notice_days":
        return _count(value, "dias")
    if name == "lock_up_months":
        return _count(value, "meses")
    if name.endswith("_amount"):
        return money(currency, value)
    return str(value) if value else EMPTY


PROFILE_TERMS = (
    ("risk_level", "Nível de risco"),
    ("target_return_spread_pct", "Retorno-alvo"),
    ("liquidity_days", "Liquidez"),
    ("max_average_term_years", "Prazo médio máximo"),
    ("eligible_asset_classes", "Classes elegíveis"),
)
FLOW_TERMS = (
    ("min_initial_amount", "Aplicação inicial mínima"),
    ("min_additional_amount", "Aplicação adicional mínima"),
    ("subscription_settlement_days", "Liquidação da aplicação"),
    ("min_redemption_amount", "Resgate mínimo"),
    ("min_balance_amount", "Saldo mínimo"),
    ("redemption_notice_days", "Aviso de resgate"),
    ("redemption_settlement_days", "Liquidação do resgate"),
    ("lock_up_months", "Carência"),
)


def term_rows(
    terms: Any, currency: str, names: tuple[tuple[str, str], ...], compare: Any = None
) -> list[dict[str, str]]:
    """Linhas (rótulo, valor) de um grupo de termos; com `compare`, o valor da outra versão."""
    rows = []
    for name, label in names:
        value = term_text(name, terms, currency)
        other = term_text(name, compare, currency) if compare is not None else value
        rows.append({"label": label, "value": value, "other": other if other != value else ""})
    return rows


def limit_rows(
    limits: Iterable[Any], options: dict[str, list[tuple[str, str]]], compare: Iterable[Any] = ()
) -> list[dict[str, str]]:
    """Limites como linhas; com `compare` (limites da outra versão), o que muda em cada uma."""
    other = {(limit.dimension, limit.target): limit for limit in compare}

    def span(item: Any) -> str:
        return f"{trimmed(item.min_pct) or '0'}% a {trimmed(item.max_pct) or '0'}%"

    rows = []
    for limit in limits:
        value = span(limit)
        match = other.get((limit.dimension, limit.target))
        changed = ""
        if other and match is None:
            changed = "sai"
        elif match is not None and (match.min_pct, match.max_pct) != (limit.min_pct, limit.max_pct):
            changed = span(match)
        rows.append(
            {
                "label": f"{DIMENSIONS[limit.dimension]}: "
                f"{limit_target_label(limit.dimension, limit.target, options)}",
                "value": value,
                "other": changed,
            }
        )
    return rows
