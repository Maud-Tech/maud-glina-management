"""Ajudas para testes. Só usado por testes (a fixture `api` está no conftest.py da raiz)."""

from typing import Any

from django.test import Client

TEST_API_KEY = "test-api-key"


class ApiClient:
    """Cliente HTTP de teste que já fala com /api/v1 autenticado."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self._client.get(
            f"/api/v1{path}",
            params or {},
            headers={"X-Api-Key": TEST_API_KEY},
        )

    def post(
        self,
        path: str,
        body: dict[str, str],
        *,
        idempotency_key: str = "pedido-1",
        api_key: str | None = TEST_API_KEY,
    ) -> Any:
        headers = {"Idempotency-Key": idempotency_key}
        if api_key is not None:
            headers["X-Api-Key"] = api_key

        return self._client.post(
            f"/api/v1{path}",
            body,
            content_type="application/json",
            headers=headers,
        )
