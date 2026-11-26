"""Gera os arquivos do Claude Code a partir da fonte única dos agentes de IA.

Fonte (edite só aqui)               Gerado (não edite)
  <pasta>/AGENTS.md            ->     <pasta>/CLAUDE.md   (uma linha: @AGENTS.md)
  .agents/skills/<nome>/...    ->     .claude/skills/<nome>/...   (cópia idêntica)

O Codex lê AGENTS.md e .agents/skills direto. O Claude Code lê CLAUDE.md e .claude/skills.

Uso:
  uv run python scripts/sync_agents.py           # gera/atualiza
  uv run python scripts/sync_agents.py --check   # só confere (usado pelo scripts/check.py)
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_SOURCE = ROOT / ".agents" / "skills"
SKILLS_TARGET = ROOT / ".claude" / "skills"
SKIP_DIRS = {".git", ".venv", ".cache", ".agents", ".claude", "node_modules", "__pycache__"}

CLAUDE_STUB = (
    "<!-- Gerado por scripts/sync_agents.py a partir do AGENTS.md ao lado. Não edite aqui. -->\n"
    "@AGENTS.md\n"
)


def instruction_dirs() -> tuple[list[Path], list[Path]]:
    """Pastas com AGENTS.md e pastas com CLAUDE.md, ignorando caches e ambientes."""
    with_agents: list[Path] = []
    with_claude: list[Path] = []
    pending = [ROOT]
    while pending:
        folder = pending.pop()
        for entry in folder.iterdir():
            if entry.is_dir() and entry.name not in SKIP_DIRS:
                pending.append(entry)
            elif entry.name == "AGENTS.md":
                with_agents.append(folder)
            elif entry.name == "CLAUDE.md":
                with_claude.append(folder)
    return sorted(with_agents), sorted(with_claude)


def expected_files() -> dict[Path, bytes]:
    """Tudo o que deveria existir do lado do Claude, com o conteúdo esperado."""
    agents_dirs, _ = instruction_dirs()
    expected = {folder / "CLAUDE.md": CLAUDE_STUB.encode() for folder in agents_dirs}
    for source in SKILLS_SOURCE.rglob("*"):
        if source.is_file() and "__pycache__" not in source.parts:
            expected[SKILLS_TARGET / source.relative_to(SKILLS_SOURCE)] = normalized(source)
    return expected


def unexpected_files(expected: dict[Path, bytes]) -> list[Path]:
    """CLAUDE.md sem AGENTS.md ao lado, ou skill que não existe mais na fonte."""
    _, claude_dirs = instruction_dirs()
    leftovers = [folder / "CLAUDE.md" for folder in claude_dirs]
    if SKILLS_TARGET.exists():
        leftovers += [path for path in SKILLS_TARGET.rglob("*") if path.is_file()]
    return sorted(path for path in leftovers if path not in expected)


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    check_only = "--check" in sys.argv
    expected = expected_files()

    outdated = [p for p, content in expected.items() if not p.exists() or normalized(p) != content]
    extra = unexpected_files(expected)

    if check_only:
        for path in outdated:
            print(f"desatualizado: {path.relative_to(ROOT).as_posix()}")
        for path in extra:
            print(f"sobrando:      {path.relative_to(ROOT).as_posix()}")
        return 1 if outdated or extra else 0

    for path in outdated:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected[path])
        print(f"gerado:   {path.relative_to(ROOT).as_posix()}")
    for path in extra:
        path.unlink()
        print(f"removido: {path.relative_to(ROOT).as_posix()}")
    if SKILLS_TARGET.exists():
        for folder in sorted(SKILLS_TARGET.rglob("*"), reverse=True):
            if folder.is_dir() and not any(folder.iterdir()):
                shutil.rmtree(folder)
    print("Sincronizado." if outdated or extra else "Já estava sincronizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
