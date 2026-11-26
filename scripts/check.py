"""CI de bolso: roda na sua máquina as mesmas verificações do CI.

Uso manual:   uv run python scripts/check.py
Automático:   o hook .githooks/pre-push chama este script com --pre-push antes de cada push.
              Instalação (uma vez por clone): git config core.hooksPath .githooks

Com --pre-push, depois dos checks ele também:
  - avisa quando o push mexe em partes sensíveis (para você avisar o time);
  - lembra de escrever no docs/journal.md quando há mudança de código sem entrada nova.
"""

import fnmatch
import shutil
import subprocess
import sys
import time

CHECKS = [
    ("Instruções dos agentes de IA sincronizadas", ["python", "scripts/sync_agents.py", "--check"]),
    ("Banco acessível e migrado", ["python", "manage.py", "migrate", "--check"]),
    ("Formatação", ["ruff", "format", "--check", "."]),
    ("Lint", ["ruff", "check", "."]),
    ("Tipos", ["mypy"]),
    ("Fronteiras entre módulos", ["lint-imports", "--no-cache"]),
    (
        "Migrations em dia com os models",
        ["python", "manage.py", "makemigrations", "--check", "--dry-run"],
    ),
    ("Testes", ["pytest", "-q"]),
]

HINTS = {
    "Instruções dos agentes de IA sincronizadas": (
        "Edite só AGENTS.md / .agents/ e gere o resto: uv run python scripts/sync_agents.py"
    ),
    "Banco acessível e migrado": (
        "Suba o banco e migre: docker compose up -d db && uv run python manage.py migrate"
    ),
    "Formatação": "Corrija com: uv run ruff format .",
    "Lint": "Muitos se corrigem com: uv run ruff check . --fix",
    "Migrations em dia com os models": "Gere a migration: uv run python manage.py makemigrations",
}

SENSITIVE = [
    "src/maud/shared/*",
    "src/maud/*/api.py",
    "src/maud/*/migrations/*",
    # Módulos críticos do projeto (ledgers, dinheiro): acrescente aqui,
    # ex.: "src/maud/modules/<modulo>/*".
    "tests/acceptance/*",
    "docs/contracts/*",
    "AGENTS.md",
    ".agents/*",
]

EMPTY_SHA = "0" * 40


def run_checks() -> bool:
    failed = []
    for name, command in CHECKS:
        executable = sys.executable if command[0] == "python" else shutil.which(command[0])
        if executable is None:
            print(f"  FALHOU  {name}: '{command[0]}' não encontrado.")
            print("          -> Rode via: uv run python scripts/check.py")
            failed.append(name)
            continue

        started = time.monotonic()
        result = subprocess.run([executable, *command[1:]], capture_output=True, text=True)
        seconds = round(time.monotonic() - started)

        if result.returncode == 0:
            print(f"  ok      {name} ({seconds}s)")
            continue

        failed.append(name)
        print(f"  FALHOU  {name} ({seconds}s)")
        output = (result.stdout + result.stderr).strip().splitlines()
        for line in output[-15:]:
            print(f"          {line}")
        if name in HINTS:
            print(f"          -> {HINTS[name]}")

    print()
    if failed:
        print(f"{len(failed)} verificação(ões) falharam: {', '.join(failed)}")
        return False
    print("Tudo certo.")
    return True


def changed_files_in_push(push_lines: list[str]) -> list[str]:
    """Lê o que o git passa ao pre-push e devolve os arquivos alterados nos commits enviados."""
    files: set[str] = set()
    for line in push_lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        _, local_sha, _, remote_sha = parts
        if local_sha == EMPTY_SHA:  # apagando branch remota
            continue
        if remote_sha == EMPTY_SHA:  # branch nova no remoto: compara com o que o remoto já tem
            commits = f"{local_sha} --not --remotes"
            listing = git(f"log --name-only --pretty=format: {commits}")
        else:
            listing = git(f"diff --name-only {remote_sha} {local_sha}")
        files.update(path for path in listing.splitlines() if path.strip())
    return sorted(files)


def git(arguments: str) -> str:
    result = subprocess.run(["git", *arguments.split()], capture_output=True, text=True)
    return result.stdout


def pre_push_reminders(files: list[str]) -> None:
    sensitive = [f for f in files if any(fnmatch.fnmatch(f, pattern) for pattern in SENSITIVE)]
    if sensitive:
        print()
        print("Este push mexe em partes sensíveis. Avise o time para alguém dar uma olhada:")
        for path in sensitive[:15]:
            print(f"  - {path}")

    touches_code = any(f.startswith("src/") for f in files)
    if touches_code and "docs/journal.md" not in files:
        print()
        print("Lembrete: nenhuma entrada nova em docs/journal.md neste push.")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    pre_push = "--pre-push" in sys.argv
    push_lines = sys.stdin.read().splitlines() if pre_push else []

    print("Verificando antes de subir..." if pre_push else "Verificando...")
    ok = run_checks()

    if pre_push and ok:
        pre_push_reminders(changed_files_in_push(push_lines))
    if pre_push and not ok:
        print("Push cancelado. Corrija e tente de novo.")
        print("(Emergência real: git push --no-verify, e registre o motivo no docs/journal.md.)")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
