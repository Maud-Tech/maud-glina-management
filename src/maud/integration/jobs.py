"""Jobs do módulo integration. Quando cada um roda está em maud/jobs/schedule.py."""

import logging

from django.conf import settings

from maud.integration.adapters.webhook.client import WebhookClient
from maud.integration.features.dispatch_outbox.handler import execute as dispatch

log = logging.getLogger(__name__)


def dispatch_outbox() -> None:
    """Entrega ao parceiro os avisos pendentes do outbox."""
    if not settings.WEBHOOK_URL:
        log.debug("WEBHOOK_URL não configurada: avisos ficam na fila")
        return

    webhook = WebhookClient(url=settings.WEBHOOK_URL, secret=settings.WEBHOOK_SECRET)
    result = dispatch(webhook)

    if result.sent or result.failed:
        log.info("outbox: %d enviados, %d falharam", result.sent, result.failed)
