"""Entregar os avisos do outbox ao parceiro. Job do Worker (não tem endpoint).

Passo a passo:
    1. trava um lote de eventos pendentes cujo horário de envio já chegou
    2. traduz cada um para o envelope do contrato
    3. envia; deu certo, marca como enviado; falhou, reagenda com espera crescente

Entrega "pelo menos uma vez": o destino ignora repetições pelo event_id.
Uma falha não segura os outros eventos do lote.
Depois de muitas falhas o evento fica "dead" e precisa de ação humana (ver shared/outbox.py).
"""

from dataclasses import dataclass

from django.db import transaction

from maud.integration.adapters.webhook.client import DeliveryError, WebhookSender
from maud.integration.adapters.webhook.mapping import to_webhook_envelope
from maud.shared import outbox


@dataclass(frozen=True)
class DispatchResult:
    sent: int
    failed: int


def execute(sender: WebhookSender, *, batch_size: int = 50) -> DispatchResult:
    sent = 0
    failed = 0

    with transaction.atomic():
        # 1. Trava o lote (outra instância pularia estes eventos)
        for event in outbox.claim_batch(limit=batch_size):
            # 2. Traduz
            envelope = to_webhook_envelope(event)

            # 3. Envia e registra o resultado
            try:
                sender.send(envelope)
            except DeliveryError as error:
                outbox.mark_failed(event, str(error))
                failed += 1
            else:
                outbox.mark_sent(event)
                sent += 1

    return DispatchResult(sent=sent, failed=failed)
