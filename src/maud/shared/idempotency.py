"""Idempotência de comandos vindos de fora (header Idempotency-Key).

Garantias:
- mesma (scope, key) + mesmo payload  → executa UMA vez; repetições devolvem a resposta gravada;
- mesma (scope, key) + payload diferente → IdempotencyConflictError (409);
- se a operação levanta exceção, nada é gravado (rollback) e a chave pode ser reusada;
- chamadas simultâneas com a mesma chave: o índice único serializa; a segunda espera a primeira.

Respostas de "recusa de negócio" (ex.: reserva recusada) devem ser DEVOLVIDAS, não levantadas,
para que fiquem gravadas e a repetição devolva a mesma recusa.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from pydantic import BaseModel

from maud.shared.errors import ConflictError
from maud.shared.models import IdempotencyRecord


class IdempotencyConflictError(ConflictError):
    code = "idempotency_key_reused"


def request_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, cls=DjangoJSONEncoder, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def run_idempotent[T: BaseModel](
    *,
    scope: str,
    key: str,
    request: Mapping[str, Any],
    response_model: type[T],
    operation: Callable[[], T],
) -> T:
    if not key or len(key) > 200:
        raise ConflictError(
            "Idempotency-Key ausente ou maior que 200 caracteres", code="invalid_idempotency_key"
        )
    digest = request_hash(request)
    with transaction.atomic():
        try:
            with transaction.atomic():  # savepoint: o IntegrityError não envenena a transação
                record = IdempotencyRecord.objects.create(scope=scope, key=key, request_hash=digest)
        except IntegrityError:
            existing = IdempotencyRecord.objects.get(scope=scope, key=key)
            if existing.request_hash != digest:
                raise IdempotencyConflictError(
                    f"Idempotency-Key '{key}' já usada com outro conteúdo"
                ) from None
            return response_model.model_validate(existing.response)

        result = operation()
        record.response = result.model_dump(mode="json")
        record.save(update_fields=["response"])
        return result
