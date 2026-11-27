"""Gravação transacional e idempotente; valida identidade e detalhe antes do commit."""

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from pydantic import BaseModel

from maud.modules.entities.registrations import RegistrationForms
from maud.shared.idempotency import run_idempotent


class RegistrationResponse(BaseModel):
    id: str


@dataclass(frozen=True)
class SaveRegistrationCommand:
    bundle: RegistrationForms
    key: str
    user_id: str
    payload: dict[str, Any]


def execute(command: SaveRegistrationCommand) -> RegistrationResponse:
    bundle = command.bundle

    def operation() -> RegistrationResponse:
        # 1. Valida todos os formulários antes da escrita.
        if not bundle.is_valid():
            raise ValidationError("Confira os campos indicados.")
        if bundle.identity != "new":
            bundle.spec.model.objects.select_for_update().get(pk=bundle.identity)
        # 2. Persiste identidade e detalhe numa única transação (run_idempotent).
        record = bundle.main.save()
        if bundle.detail is not None:
            detail = bundle.detail.save(commit=False)
            setattr(detail, bundle.spec.detail_parent, record)
            try:
                detail.full_clean()
            except ValidationError as error:
                bundle.add_detail_errors(error)
                raise
            detail.save()
        # Endereços e contatos participam da mesma transação da identidade.
        for _, formset in bundle.related:
            items = formset.save(commit=False)
            for removed in formset.deleted_objects:
                removed.delete()
            # Libera os marcadores antigos antes de trocar o item principal.
            changed_ids = [item.pk for item in items if item.pk]
            formset.model.objects.filter(entity=record, pk__in=changed_ids, is_primary=True).update(
                is_primary=False
            )
            for item in items:
                item.entity = record
                try:
                    item.full_clean()
                except ValidationError as error:
                    target_form = next(form for form in formset.forms if form.instance is item)
                    for name, errors in getattr(
                        error, "message_dict", {"__all__": error.messages}
                    ).items():
                        for message in errors:
                            target_form.add_error(
                                name if name in target_form.fields else None, message
                            )
                    raise
                item.save()
        # 3. Cadastro local: nenhum fato é publicado para sistemas externos.
        return RegistrationResponse(id=str(record.pk))

    return run_idempotent(
        scope="entities.save_registration:"
        + command.user_id
        + ":"
        + bundle.resource
        + ":"
        + bundle.identity,
        key=command.key,
        request=command.payload,
        response_model=RegistrationResponse,
        operation=operation,
    )
