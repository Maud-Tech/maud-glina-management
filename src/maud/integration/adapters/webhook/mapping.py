"""Tradução: nosso evento do outbox → envelope que o parceiro recebe no webhook.

Formato descrito no contrato do parceiro (docs/contracts/).
"""

from typing import Any

from maud.shared.models import OutboxEvent


def to_webhook_envelope(event: OutboxEvent) -> dict[str, Any]:
    return {
        "event_id": str(event.id),  # o destino usa para ignorar entregas repetidas
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat(),
        "aggregate": {
            "type": event.aggregate_type,
            "id": event.aggregate_id,
        },
        "payload": event.payload,
    }
