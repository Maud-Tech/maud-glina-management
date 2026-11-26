"""Configuração comum a todos os testes (src/ e tests/)."""

import os
from collections.abc import Iterator

import pytest
from django.test import Client, override_settings

from maud.shared.testing import TEST_API_KEY, ApiClient

# Hypothesis grava exemplos em .cache/hypothesis (junto dos outros caches), não na raiz.
os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", ".cache/hypothesis")


@pytest.fixture
def api(client: Client) -> Iterator[ApiClient]:
    """Cliente da API já autenticado com uma chave de teste."""
    with override_settings(MAUD_API_KEYS=[TEST_API_KEY]):
        yield ApiClient(client)
