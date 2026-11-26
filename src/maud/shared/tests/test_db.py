import pytest
from django.db import DatabaseError, connection, transaction

from maud.shared.db import append_only_sql

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


def test_table_name_is_validated() -> None:
    with pytest.raises(ValueError):
        append_only_sql("x; DROP TABLE y")
