"""Hook PreToolUse: impede alterar ou apagar testes EXISTENTES em tests/acceptance/.

Criar arquivo novo é permitido. Exit code 2 bloqueia a ferramenta e devolve a mensagem ao agente.
Serve aos dois agentes (mesmo formato de hook, entrada diferente):
  - Claude Code (Edit/Write/MultiEdit): tool_input.file_path
  - Codex (apply_patch): tool_input.command com o patch ("*** Update File: <caminho>" etc.)

Ligado em .claude/settings.json e .codex/hooks.json.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PROTECTED = Path("tests") / "acceptance"

# Linhas de cabeçalho do apply_patch que mexem em arquivo existente. "Add File" é permitido.
PATCH_TOUCHES_EXISTING = re.compile(r"^\*\*\* (?:Update|Delete) File: (.+?)\s*$", re.MULTILINE)


def project_root(cwd: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else cwd


def targets(tool_input: dict[str, object]) -> list[str]:
    file_path = tool_input.get("file_path")
    if isinstance(file_path, str) and file_path:
        return [file_path]
    command = tool_input.get("command")
    if isinstance(command, str) and "*** Begin Patch" in command:
        return PATCH_TOUCHES_EXISTING.findall(command)
    return []


def protected_existing(path: str, cwd: Path, root: Path) -> Path | None:
    target = Path(path)
    if not target.is_absolute():
        target = cwd / target
    target = target.resolve()
    try:
        relative = target.relative_to(root / PROTECTED)
    except ValueError:
        return None
    if target.exists() and relative.name != "__init__.py":
        return PROTECTED / relative
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    cwd = Path(event.get("cwd") or ".").resolve()
    root = project_root(cwd).resolve()
    blocked = [p for path in targets(tool_input) if (p := protected_existing(path, cwd, root))]
    if not blocked:
        return 0

    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    names = ", ".join(path.as_posix() for path in blocked)
    sys.stderr.write(
        f"BLOQUEADO: {names} é teste de aceitação existente (oráculo). "
        "Não altere cenários existentes para fazer código passar. "
        "Se o código falha, corrija o código. Se o cenário parece errado, PARE e explique ao "
        "humano. Cenário novo pode ser criado em arquivo novo.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
