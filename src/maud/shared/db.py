"""Proteções no banco para tabelas financeiras.

Migration não vai para o git (ADR "Migrations fora do git"), então a proteção não mora em
migration: o sinal `post_migrate` (ver `apps.py`) a aplica a cada `migrate`, inclusive no
banco de teste.

Ledger (tabela de lançamentos) marca o model:

    from maud.shared.db import append_only

    @append_only
    class LedgerEntry(models.Model):
        ...

Depois de cada `migrate`, a função `maud_forbid_mutation()` é criada (ou recriada) e cada
tabela marcada ganha os triggers que recusam UPDATE, DELETE e TRUNCATE.

Exceção só do banco de teste: o Django limpa o banco com TRUNCATE entre os testes de transação
real. O `conftest.py` da raiz liga `maud.allow_test_truncate` no banco de teste, e só o TRUNCATE
passa. UPDATE e DELETE continuam recusados, em teste e em produção.
"""

import re
from typing import Any

from django.db import DEFAULT_DB_ALIAS, connections, models, transaction

FORBID_MUTATION_FUNCTION = """
CREATE OR REPLACE FUNCTION maud_forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'TRUNCATE' AND current_setting('maud.allow_test_truncate', true) = 'on' THEN
        RETURN NULL;
    END IF;
    RAISE EXCEPTION 'tabela % é append-only: corrija com estorno, não com %', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'P0001';
END;
$$;
"""

# Chave que só o banco de teste liga (conftest.py da raiz): deixa o TRUNCATE do Django passar.
TEST_TRUNCATE_SETTING = "maud.allow_test_truncate"

# Ainda importado pela migration 0002 que ficou na máquina de quem já tinha o banco.
DROP_FORBID_MUTATION_FUNCTION = "DROP FUNCTION IF EXISTS maud_forbid_mutation();"

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def append_only_sql(table: str) -> tuple[str, str]:
    """(forward, reverse) SQL que bloqueia UPDATE, DELETE e TRUNCATE em `table`."""
    if not _IDENTIFIER.match(table):
        raise ValueError(f"nome de tabela inválido: {table!r}")
    forward = f"""
        CREATE TRIGGER {table}_no_update_delete
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION maud_forbid_mutation();
        CREATE TRIGGER {table}_no_truncate
            BEFORE TRUNCATE ON {table}
            FOR EACH STATEMENT EXECUTE FUNCTION maud_forbid_mutation();
    """
    reverse = f"""
        DROP TRIGGER IF EXISTS {table}_no_update_delete ON {table};
        DROP TRIGGER IF EXISTS {table}_no_truncate ON {table};
    """
    return forward, reverse


_APPEND_ONLY_MODELS: list[type[models.Model]] = []


def append_only[Model: type[models.Model]](model: Model) -> Model:
    """Marca o model como ledger: o banco recusa UPDATE, DELETE e TRUNCATE na tabela dele."""
    if model not in _APPEND_ONLY_MODELS:
        _APPEND_ONLY_MODELS.append(model)
    return model


def append_only_tables() -> list[str]:
    """Tabelas dos models marcados com `@append_only`."""
    return sorted({model._meta.db_table for model in _APPEND_ONLY_MODELS})


def apply_protections(*, using: str = DEFAULT_DB_ALIAS, **_: Any) -> None:
    """Cria a função e os triggers dos ledgers. Ligado ao `post_migrate`; pode rodar de novo."""
    connection = connections[using]
    existing = set(connection.introspection.table_names())
    with transaction.atomic(using=using), connection.cursor() as cursor:
        cursor.execute(FORBID_MUTATION_FUNCTION)
        for table in append_only_tables():
            if table not in existing:
                continue
            forward, reverse = append_only_sql(table)
            cursor.execute(reverse)
            cursor.execute(forward)
