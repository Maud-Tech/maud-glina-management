"""Configuração comum a todos os testes (src/ e tests/)."""

import os
from collections.abc import Iterator
from typing import Any

import pytest
from django.db import connection
from django.test import Client, override_settings

from maud.shared.db import TEST_TRUNCATE_SETTING
from maud.shared.testing import TEST_API_KEY, ApiClient

# Hypothesis grava exemplos em .cache/hypothesis (junto dos outros caches), não na raiz.
os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", ".cache/hypothesis")


@pytest.fixture
def api(client: Client) -> Iterator[ApiClient]:
    """Cliente da API já autenticado com uma chave de teste."""
    with override_settings(MAUD_API_KEYS=[TEST_API_KEY]):
        yield ApiClient(client)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup: None, django_db_blocker: Any) -> None:
    """Banco de teste aceita o TRUNCATE do Django nos ledgers (limpeza entre testes de transação).

    Só no banco de teste: UPDATE e DELETE continuam recusados (ver `maud.shared.db`).
    """
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        name = connection.ops.quote_name(connection.settings_dict["NAME"])
        cursor.execute(f"ALTER DATABASE {name} SET {TEST_TRUNCATE_SETTING} = 'on'")
        cursor.execute(f"SET {TEST_TRUNCATE_SETTING} = 'on'")
