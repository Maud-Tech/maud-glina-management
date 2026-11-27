FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev

# Migrations: vêm da pasta do projeto, não do git (ADR "Migrations fora do git"). A imagem
# leva as que estão na máquina de quem faz o build. O build falha se algum model mudou e a
# migration não foi gerada antes: o banco não recebe um histórico que não bate com os models.
RUN DJANGO_DEBUG=true python manage.py makemigrations --check --dry-run

# Arquivos estáticos (casca das telas e admin) prontos na imagem, em staticfiles/.
RUN DJANGO_DEBUG=true python manage.py collectstatic --noinput

EXPOSE 8080
