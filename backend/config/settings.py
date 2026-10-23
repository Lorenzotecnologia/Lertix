import os
from decimal import Decimal
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Defina DJANGO_SECRET_KEY para executar com DJANGO_DEBUG=false."
        )
    SECRET_KEY = "django-insecure-local-development-only"

CANONICAL_HOST = os.environ.get("CANONICAL_HOST", "")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]"
    ).split(",")
    if host.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

CODESPACE_NAME = os.environ.get("CODESPACE_NAME")
if DEBUG and CODESPACE_NAME:
    codespace_domain = os.environ.get(
        "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev"
    )
    CSRF_TRUSTED_ORIGINS += [
        f"https://{CODESPACE_NAME}-8000.{codespace_domain}",
        "https://localhost:8000",
        "https://127.0.0.1:8000",
    ]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.CanonicalHostMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured(
        "Defina DATABASE_URL para executar em produção."
    )

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# E-mail via SMTP da Locaweb (conta de e-mail do domínio). Sem EMAIL_HOST_PASSWORD
# as mensagens são apenas escritas no log.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "email-ssl.com.br")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "465"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_USE_TLS = not EMAIL_USE_SSL
EMAIL_TIMEOUT = 10
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "contato@lertrix.com"
)
CONTACT_EMAIL_TO = os.environ.get("CONTACT_EMAIL_TO", DEFAULT_FROM_EMAIL)

# Número com DDI e DDD, só dígitos (ex.: 5511999998888). Vazio oculta os botões.
WHATSAPP_NUMBER = "".join(c for c in os.environ.get("WHATSAPP_NUMBER", "5511983831766") if c.isdigit())

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR.parent / "frontend" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Vitrine somente informativa: com STORE_ENABLED=false, carrinho, frete, pedido e Pix
# ficam desativados (404) e os botões de compra são ocultados.
STORE_ENABLED = os.environ.get("STORE_ENABLED", "true").strip().lower() not in {
    "0", "false", "no", "off",
}

# Pix direto (sem intermediador). A chave é a conta que recebe os pagamentos.
PIX_KEY = os.environ.get("PIX_KEY", "51835078000248")
PIX_RECEIVER_NAME = os.environ.get(
    "PIX_RECEIVER_NAME", "Rotatek Tecnologia de Impressao Ltda"
)
PIX_RECEIVER_CITY = os.environ.get("PIX_RECEIVER_CITY", "Barueri")

# Frete: CEP de origem (Barueri/SP), mínimo para frete grátis (vazio = sem frete grátis) e peso padrão por livro.
SHIPPING_ORIGIN_CEP = os.environ.get("SHIPPING_ORIGIN_CEP", "06455-010")
_free_min = os.environ.get("FREE_SHIPPING_MIN", "").replace(",", ".")
FREE_SHIPPING_MIN = Decimal(_free_min) if _free_min else None
DEFAULT_BOOK_WEIGHT_GRAMS = int(os.environ.get("DEFAULT_BOOK_WEIGHT_GRAMS", "500"))


def _optional_positive_int(name):
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} deve ser um número inteiro positivo.") from exc
    if number <= 0:
        raise ImproperlyConfigured(f"{name} deve ser um número inteiro positivo.")
    return number


CORREIOS_API_BASE_URL = os.environ.get(
    "CORREIOS_API_BASE_URL", "https://api.correios.com.br"
).rstrip("/")
CORREIOS_API_TIMEOUT = int(os.environ.get("CORREIOS_API_TIMEOUT", "8"))
CORREIOS_USERNAME = os.environ.get("CORREIOS_USERNAME", "")
CORREIOS_ACCESS_CODE = os.environ.get("CORREIOS_ACCESS_CODE", "")
CORREIOS_POSTING_CARD = os.environ.get("CORREIOS_POSTING_CARD", "")
CORREIOS_PAC_CODE = os.environ.get("CORREIOS_PAC_CODE", "")
CORREIOS_SEDEX_CODE = os.environ.get("CORREIOS_SEDEX_CODE", "")
CORREIOS_PACKAGE_LENGTH_CM = _optional_positive_int("CORREIOS_PACKAGE_LENGTH_CM")
CORREIOS_PACKAGE_WIDTH_CM = _optional_positive_int("CORREIOS_PACKAGE_WIDTH_CM")
CORREIOS_PACKAGE_HEIGHT_CM = _optional_positive_int("CORREIOS_PACKAGE_HEIGHT_CM")
