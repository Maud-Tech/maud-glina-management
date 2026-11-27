#!/usr/bin/env python
import os
import sys
from pathlib import Path

# O código fica em src/. Com uv o projeto já vem instalado; com pip -r requirements.txt não,
# então o manage.py acha o pacote `maud` sozinho, de qualquer jeito que o ambiente foi criado.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maud.config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
