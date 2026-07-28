from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# --- Apps -------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_htmx",
    "drf_spectacular",
    "axes",
]

LOCAL_APPS = [
    "apps.core",
    "apps.tenants",
    "apps.accounts",
    "apps.authentication",
    "apps.audit",
    "apps.platform_admin",
    "apps.branding",
    "apps.clients",
    "apps.staff",
    "apps.services",
    "apps.scheduling",
    "apps.finance",
    "apps.reports",
    "apps.dashboard",
    "apps.notifications",
    "apps.calendar_sync",
    "apps.verticals.barber",
    "apps.verticals.dentistry",
    "apps.verticals.psychology",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Middleware ---------------------------------------------------------
# TenantResolutionMiddleware roda logo após a sessão e antes de qualquer
# autenticação, para que request.tenant já exista quando o backend de auth
# customizado (apps.accounts.backends.TenantAwareBackend) precisar dele.
# AxesMiddleware precisa ser o último, conforme documentação do django-axes.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "apps.tenants.middleware.TenantResolutionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.branding.context_processors.branding",
                "apps.verticals.context_processors.verticals",
            ],
        },
    },
]

# --- Banco de dados -------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth / Multi-tenant --------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "apps.accounts.backends.TenantAwareBackend",
]

LOGIN_URL = "authentication:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "authentication:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Domínio administrativo do Super Admin (cross-tenant) e domínio base para
# resolução de subdomínio (empresa.<TENANT_BASE_DOMAIN>). TENANT_BYPASS_HOSTS
# existe só por conveniência de desenvolvimento local e deve ficar vazio em
# produção (ver config/settings/production.py).
PLATFORM_ADMIN_HOST = env("PLATFORM_ADMIN_HOST", default="admin.syncora.local")
TENANT_BASE_DOMAIN = env("TENANT_BASE_DOMAIN", default="syncora.local")
TENANT_BYPASS_HOSTS = env.list("TENANT_BYPASS_HOSTS", default=["localhost", "127.0.0.1"])

# Chave de criptografia (Fernet) para tokens OAuth de terceiros em repouso —
# ver apps/core/fields.py:EncryptedTextField. Não é a mesma coisa que
# SECRET_KEY (rotacionar uma não deve depender da outra).
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")

# Sincronização de calendário externo (Google/Outlook) — ver
# apps/calendar_sync/providers.py. Credenciais em branco por padrão: os
# botões de conectar aparecem, mas falham com mensagem clara em vez de
# quebrar a aplicação até você gerar as credenciais reais.
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")
GOOGLE_OAUTH_CLIENT_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET", default="")
MICROSOFT_OAUTH_CLIENT_ID = env("MICROSOFT_OAUTH_CLIENT_ID", default="")
MICROSOFT_OAUTH_CLIENT_SECRET = env("MICROSOFT_OAUTH_CLIENT_SECRET", default="")
# Host fixo do callback OAuth — Google/Microsoft exigem um redirect_uri
# cadastrado antecipadamente e idêntico a cada chamada, então não dá pra
# usar o subdomínio dinâmico de cada empresa. Fica fora da resolução de
# tenant (mesmo tratamento do PLATFORM_ADMIN_HOST) e redireciona de volta
# para o subdomínio certo assim que a conexão é concluída.
CALENDAR_SYNC_HOST = env("CALENDAR_SYNC_HOST", default="connect.syncora.app")
CALENDAR_SYNC_CALLBACK_BASE_URL = env(
    "CALENDAR_SYNC_CALLBACK_BASE_URL", default=f"https://{CALENDAR_SYNC_HOST}"
)

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hora
AXES_RESET_ON_SUCCESS = True
# Padrão do django-axes é bloquear só por IP — isso bloqueia todo mundo atrás
# do mesmo NAT/proxy corporativo quando uma única conta erra a senha 5 vezes.
# Bloquear por (username, IP) é o recomendado para não gerar esse efeito colateral.
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]

# --- DRF / JWT --------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Syncora API",
    "DESCRIPTION": "API do Syncora — SaaS multi-tenant de agendamento e gestão empresarial.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGIN_REGEXES = [
    rf"^https?://([a-zA-Z0-9-]+\.)?{TENANT_BASE_DOMAIN.replace('.', r'\.')}$",
]

# --- Cache / Redis ---------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# --- Celery -----------------------------------------------------------

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"

# Agendamento das tasks de notificação (exige um worker + beat rodando de
# verdade — nenhum dos dois está ativo neste ambiente de desenvolvimento;
# isso aqui é a configuração pronta para quando existir).
CELERY_BEAT_SCHEDULE = {
    "send-appointment-reminders": {
        "task": "apps.notifications.tasks.send_appointment_reminders",
        "schedule": crontab(minute=0),  # a cada hora
    },
    "send-birthday-greetings": {
        "task": "apps.notifications.tasks.send_birthday_greetings",
        "schedule": crontab(hour=8, minute=0),  # todo dia às 8h
    },
    "send-return-reminders": {
        "task": "apps.notifications.tasks.send_return_reminders",
        "schedule": crontab(hour=9, minute=0),  # todo dia às 9h
    },
}

# --- E-mail -------------------------------------------------------------

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@syncora.app")

# --- Internacionalização ------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("pt-br", "Português (Brasil)"),
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# --- Arquivos estáticos e mídia ------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static" / "dist"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Logging -------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "syncora.audit": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
