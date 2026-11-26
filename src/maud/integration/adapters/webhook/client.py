"""Transporte: envia um envelope para o webhook do parceiro. Não decide nada, só entrega.

Assinatura: se houver segredo configurado, o corpo vai assinado com HMAC-SHA256 no header
X-Maud-Signature. O formato fica descrito no contrato do parceiro (docs/contracts/).
"""

import hashlib
import hmac
import json
import urllib.error
import urllib.request
from typing import Any, Protocol

from django.core.serializers.json import DjangoJSONEncoder

TIMEOUT_SECONDS = 10


class DeliveryError(Exception):
    """O destino não confirmou o recebimento (erro de rede ou resposta fora de 2xx)."""


class WebhookSender(Protocol):
    def send(self, envelope: dict[str, Any]) -> None: ...


class WebhookClient:
    def __init__(self, url: str, secret: str = "") -> None:
        self._url = url
        self._secret = secret

    def send(self, envelope: dict[str, Any]) -> None:
        body = json.dumps(envelope, cls=DjangoJSONEncoder).encode()

        headers = {
            "Content-Type": "application/json",
            "X-Maud-Event-Id": str(envelope["event_id"]),
        }
        if self._secret:
            signature = hmac.new(self._secret.encode(), body, hashlib.sha256).hexdigest()
            headers["X-Maud-Signature"] = f"sha256={signature}"

        request = urllib.request.Request(self._url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            raise DeliveryError(f"O destino respondeu {error.code}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise DeliveryError(f"Falha de rede ao entregar o webhook: {error}") from error

        if not 200 <= status < 300:
            raise DeliveryError(f"O destino respondeu {status}")
