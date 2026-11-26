"""Autenticação da API: chave no header X-Api-Key.

Ponto único de autenticação: trocar o esquema (HMAC, mTLS, OAuth) aqui não muda nenhuma slice.
O esquema combinado com cada parceiro fica no contrato dele (docs/contracts/).
"""

import hmac

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyHeader


class ApiKey(APIKeyHeader):
    param_name = "X-Api-Key"

    def authenticate(self, request: HttpRequest, key: str | None) -> str | None:
        if not key:
            return None
        for accepted in settings.MAUD_API_KEYS:
            if hmac.compare_digest(key.encode(), accepted.encode()):
                return "api-client"
        return None
