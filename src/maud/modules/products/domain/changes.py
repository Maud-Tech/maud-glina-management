"""Diferença entre dois retratos de um registro, para o histórico (antes e depois por campo)."""

from collections.abc import Mapping


def changed_fields(
    before: Mapping[str, object], after: Mapping[str, object]
) -> dict[str, list[object]]:
    """{campo: [antes, depois]} só dos campos que mudaram. Campo ausente vale None."""
    return {
        name: [before.get(name), after.get(name)]
        for name in sorted(set(before) | set(after))
        if before.get(name) != after.get(name)
    }
