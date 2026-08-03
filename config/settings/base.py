import re
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
    "apps.authentication.middleware.IdleSessionTimeoutMiddleware",
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
                "apps.core.context_processors.shell",
            ],
        },
    },
]

# --- Banco de dados -------------------------------------------------------
# Railway (e a maioria dos provedores gerenciados) injeta uma única
# DATABASE_URL, em vez das variáveis DB_* separadas usadas em dev local.
# dj_database_url só é importado quando DATABASE_URL existe de fato, então
# continua sem exigir esse pacote instalado em ambientes de desenvolvimento.
DATABASE_URL = env("DATABASE_URL", default="")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
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
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "authentication:login"

# Django, por padrão, não desloga por inatividade -- o cookie de sessão é
# "rolante": qualquer request autenticada recalcula o vencimento pra daqui a
# SESSION_COOKIE_AGE (2 semanas), então uma pessoa que visita o site pelo
# menos 1x a cada 2 semanas nunca é deslogada de verdade. Corrigido por
# apps/authentication/middleware.py:IdleSessionTimeoutMiddleware, que desloga
# de verdade depois desse tanto de segundos sem nenhuma request autenticada.
SESSION_IDLE_TIMEOUT_SECONDS = env.int("SESSION_IDLE_TIMEOUT_SECONDS", default=1800)

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
# Site de cadastro self-service (apps/onboarding) — não confundir com o site
# de marketing/institucional (esse é estático, hospedado à parte no Netlify,
# fora do Django inteiramente — ver docs de deploy no README). Fica num
# subdomínio (ex.: "app.syncora.app"), não no domínio apex, porque em
# produção o apex aponta pro Netlify e o Django responde só pelo wildcard
# *.TENANT_BASE_DOMAIN.
MARKETING_HOST = env("MARKETING_HOST", default="app.syncora.app")

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
        "apps.core.permissions.HasTenantMembership",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.api.throttling.PlanRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Usados só como piso de segurança para usuários sem tenant
        # resolvido (ex.: platform admin) — o limite por empresa de
        # verdade vem do Plan (ver apps/api/throttling.py).
        "user": "300/min",
        "anon": "20/min",
    },
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

# Precisa cobrir os 4 hosts especiais do TenantResolutionMiddleware, não só
# TENANT_BASE_DOMAIN — nos valores padrão de dev/exemplo eles coincidem por
# serem subdomínios do mesmo domínio, mas isso não é garantido (ex.:
# MARKETING_HOST pode ser um domínio completamente diferente).
_CORS_HOSTS = {TENANT_BASE_DOMAIN, PLATFORM_ADMIN_HOST, MARKETING_HOST, CALENDAR_SYNC_HOST}
CORS_ALLOWED_ORIGIN_REGEXES = [
    rf"^https?://([a-zA-Z0-9-]+\.)?{re.escape(host)}$" for host in _CORS_HOSTS
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

# Agendamento das tasks periódicas (exige um worker + beat rodando de
# verdade — ver README para como subir os dois processos).
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
    "sync-external-calendars": {
        "task": "apps.calendar_sync.tasks.sync_all_calendars",
        "schedule": crontab(minute="*/15"),  # a cada 15 minutos
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
# "dist" é a saída do pipeline Tailwind CLI (ainda não construído — Fase 4b
# pendente, ver templates/base.html); "src" já serve hoje os assets que não
# precisam de build (ícones do PWA, manifest, service worker).
STATICFILES_DIRS = [BASE_DIR / "static" / "dist", BASE_DIR / "static" / "src"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Upload de arquivos (logos, fotos de cliente/profissional, documentos) —
# por padrão fica no disco local (STATIC_ROOT/MEDIA_ROOT), o que funciona em
# dev mas não é durável nem escalável num servidor de aplicação stateless
# (o disco se perde a cada deploy/restart em serviços como o Railway sem
# volume). Se AWS_STORAGE_BUCKET_NAME estiver definido, troca para
# armazenamento S3-compatível (AWS S3, Cloudflare R2, Backblaze B2 — todos
# falam o mesmo protocolo) via django-storages; sem isso configurado, a
# aplicação continua funcionando normalmente com disco local, mesmo padrão
# usado para OAuth/Sentry (build pronto, credencial real fica pro usuário).
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}
if AWS_STORAGE_BUCKET_NAME:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="auto")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}

# --- Logging -------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
        # Usado em produção (ver config/settings/production.py) — uma linha
        # JSON por evento, para ferramentas de agregação de log.
        "json": {"()": "apps.core.logging_utils.JSONFormatter"},
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
        "syncora.notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "syncora.calendar_sync": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
