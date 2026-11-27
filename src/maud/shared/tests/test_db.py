import pytest
from django.db import DatabaseError, connection, transaction

from maud.shared.db import TEST_TRUNCATE_SETTING, append_only_sql

pytestmark = pytest.mark.django_db


def test_append_only_table_accepts_insert_and_rejects_update_and_delete() -> None:
    forward, _ = append_only_sql("tmp_ledger")
    with connection.cursor() as cur:
        cur.execute("CREATE TABLE tmp_ledger (id int primary key, qty numeric(28,8))")
        cur.execute(forward)
        cur.execute("INSERT INTO tmp_ledger VALUES (1, 10)")

        for statement in ("UPDATE tmp_ledger SET qty = 0", "DELETE FROM tmp_ledger"):
            with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
                cur.execute(statement)

        cur.execute("SELECT qty FROM tmp_ledger WHERE id = 1")
        assert cur.fetchone()[0] == 10


def test_truncate_is_rejected_unless_the_test_database_switch_is_on() -> None:
    """Produção nunca liga a chave; o banco de teste liga só para a limpeza do Django."""
    forward, _ = append_only_sql("tmp_ledger_truncate")
    with connection.cursor() as cur:
        cur.execute("CREATE TABLE tmp_ledger_truncate (id int primary key)")
        cur.execute(forward)
        cur.execute("INSERT INTO tmp_ledger_truncate VALUES (1)")

        with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
            cur.execute(f"SET LOCAL {TEST_TRUNCATE_SETTING} = 'off'")
            cur.execute("TRUNCATE tmp_ledger_truncate")

        with transaction.atomic():
            cur.execute(f"SET LOCAL {TEST_TRUNCATE_SETTING} = 'on'")
            cur.execute("TRUNCATE tmp_ledger_truncate")
            cur.execute("INSERT INTO tmp_ledger_truncate VALUES (2)")
            with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
                cur.execute("DELETE FROM tmp_ledger_truncate")


def test_table_name_is_validated() -> None:
    with pytest.raises(ValueError):
        append_only_sql("x; DROP TABLE y")
