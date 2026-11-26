"""Tabelas de infraestrutura compartilhada. A lógica fica em idempotency.py e outbox.py."""

import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class IdempotencyRecord(models.Model):
    """Uma linha por (scope, key). Repetir a mesma chave devolve a mesma resposta."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=100)
    key = models.CharField(max_length=200)
    request_hash = models.CharField(max_length=64)
    response = models.JSONField(null=True, encoder=DjangoJSONEncoder)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scope", "key"], name="uq_idempotency_scope_key")
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.key}"


class OutboxEvent(models.Model):
    """Evento a entregar para fora (parceiros). Gravado na MESMA transação do fato que o gerou."""

    class Status(models.TextChoices):
        PENDING = "pending"
        SENT = "sent"
        DEAD = "dead"  # esgotou as tentativas: exige ação humana

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=120)
    aggregate_type = models.CharField(max_length=60)
    aggregate_id = models.CharField(max_length=64)
    payload = models.JSONField(encoder=DjangoJSONEncoder)
    occurred_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField()
    last_error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "next_attempt_at"], name="ix_outbox_due")]

    def __str__(self) -> str:
        return f"{self.event_type} {self.aggregate_type}:{self.aggregate_id}"
