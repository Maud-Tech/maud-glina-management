"""Versão de teste do webhook: guarda o que seria enviado, sem internet."""

from typing import Any

from maud.integration.adapters.webhook.client import DeliveryError


class FakeWebhookClient:
    def __init__(self, *, failures_before_success: int = 0) -> None:
        self.sent: list[dict[str, Any]] = []
        self._failures_left = failures_before_success

    def send(self, envelope: dict[str, Any]) -> None:
        if self._failures_left > 0:
            self._failures_left -= 1
            raise DeliveryError("falha simulada")
        self.sent.append(envelope)
