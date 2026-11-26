"""Proíbe float no código de produção: dinheiro e shares são sempre Decimal.

Pega literal (1.5), conversão (float(x)) e anotação (x: float). Para tempo use timedelta/int.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "maud"


def _offenses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            found.append(f"{path}:{node.lineno} literal float {node.value!r}")
        elif isinstance(node, ast.Name) and node.id == "float":
            found.append(f"{path}:{node.lineno} uso de 'float'")
    return found


def test_production_code_does_not_use_float() -> None:
    files = [
        p
        for p in SRC.rglob("*.py")
        if "migrations" not in p.parts and not p.name.startswith("test_")
    ]
    assert files, "nenhum arquivo encontrado: caminho errado?"
    offenses = [o for f in files for o in _offenses(f)]
    assert offenses == [], "\n".join(offenses)
