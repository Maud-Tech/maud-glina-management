"""Proteções no banco para tabelas financeiras. Use em migrations.

Exemplo numa migration de ledger:

    from maud.shared.db import append_only

    operations = [
        migrations.CreateModel(name="LedgerEntry", ...),
        append_only("<app>_ledgerentry"),  # tabela = <label do app>_<model em minúsculas>
    ]

A função `maud_forbid_mutation()` é criada pela migration 0002 de maud.shared, então a
migration do ledger precisa depender dela: ("shared", "0002_forbid_mutation_function").
"""

import re

from django.db import migrations

FORBID_MUTATION_FUNCTION = """
CREATE OR REPLACE FUNCTION maud_forbid_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'tabela % é append-only: corrija com estorno, não com %', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'P0001';
END;
$$;
"""

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


def append_only(table: str) -> migrations.RunSQL:
    forward, reverse = append_only_sql(table)
    return migrations.RunSQL(forward, reverse)
