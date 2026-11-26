"""Testa o cliente HTTP de verdade contra um servidor local (sem internet)."""

import hashlib
import hmac
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from maud.integration.adapters.webhook.client import DeliveryError, WebhookClient

ENVELOPE = {"event_id": "e-1", "event_type": "example.item_created", "payload": {}}


class FakeWebhookServer:
    """Servidor HTTP local que responde com `status` e guarda o último pedido."""

    def __init__(self) -> None:
        self.status = 200
        self.received_headers: dict[str, str] = {}
        self.received_body = b""
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers["Content-Length"])
                fake.received_body = self.rfile.read(length)
                fake.received_headers = dict(self.headers)
                self.send_response(fake.status)
                self.end_headers()

            def log_message(self, *args: Any) -> None:  # silencia o log no terminal
                pass

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_port}/webhook"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self._server.shutdown()


@pytest.fixture
def webhook_server() -> Iterator[FakeWebhookServer]:
    server = FakeWebhookServer()
    yield server
    server.stop()


def test_client_signs_body_with_hmac_when_secret_is_set(
    webhook_server: FakeWebhookServer,
) -> None:
    client = WebhookClient(url=webhook_server.url, secret="segredo-de-teste")

    client.send(ENVELOPE)

    expected = hmac.new(b"segredo-de-teste", webhook_server.received_body, hashlib.sha256)
    assert webhook_server.received_headers["X-Maud-Signature"] == f"sha256={expected.hexdigest()}"
    assert webhook_server.received_headers["X-Maud-Event-Id"] == "e-1"


def test_non_2xx_response_counts_as_failure(webhook_server: FakeWebhookServer) -> None:
    webhook_server.status = 500
    client = WebhookClient(url=webhook_server.url)

    with pytest.raises(DeliveryError, match="500"):
        client.send(ENVELOPE)
