"""Configuração Django. Tudo que muda por ambiente vem de variável de ambiente."""

import os
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


BASE_DIR = Path(__file__).resolve().parents[3]


def _load_dotenv(path: Path) -> None:
    """Lê .env local (só desenvolvimento). Variável já definida no ambiente sempre vence."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        os.environ.setdefault(name.strip(), value.strip())


_load_dotenv(BASE_DIR / ".env")

DEBUG = _env_bool("DJANGO_DEBUG", default=False)
SECRET_KEY = _env("DJANGO_SECRET_KEY") or ("dev-only-insecure-key" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY é obrigatória fora de DEBUG")
ALLOWED_HOSTS = [
    h.strip() for h in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h
]

# Chaves de API aceitas no header X-Api-Key (ver maud.shared.http).
MAUD_API_KEYS = [k.strip() for k in _env("MAUD_API_KEYS").split(",") if k.strip()]
if DEBUG and not MAUD_API_KEYS:
    MAUD_API_KEYS = ["dev-key"]

# Webhook de saída (avisos do outbox). Sem URL, os avisos ficam na fila até configurar.
WEBHOOK_URL = _env("WEBHOOK_URL")
WEBHOOK_SECRET = _env("WEBHOOK_SECRET")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja",
    # Módulos, de baixo para cima (mesma ordem das camadas do import-linter).
    "maud.shared",
    "maud.modules.entities",
    "maud.modules.example",
    "maud.jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "maud.config.urls"
WSGI_APPLICATION = "maud.config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": _env("POSTGRES_HOST", "localhost"),
        "PORT": _env("POSTGRES_PORT", "5435"),
        "NAME": _env("POSTGRES_DB", "maud_glina_management"),
        "USER": _env("POSTGRES_USER", "maud"),
        "PASSWORD": _env("POSTGRES_PASSWORD", "maud"),
        "ATOMIC_REQUESTS": False,  # transações são explícitas nos handlers
        "CONN_MAX_AGE": 60,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"  # tudo gravado em UTC; data-base é campo date explícito
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": _env("LOG_LEVEL", "INFO")},
}
