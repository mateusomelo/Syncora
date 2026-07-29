from .base import *  # noqa: F401,F403

DEBUG = False

TENANT_BASE_DOMAIN = env("TENANT_BASE_DOMAIN", default="syncora.app")  # noqa: F405
PLATFORM_ADMIN_HOST = env("PLATFORM_ADMIN_HOST", default="admin.syncora.app")  # noqa: F405
# Em produção, todo host precisa resolver para um tenant real ou para o
# domínio administrativo — nenhum atalho de conveniência.
TENANT_BYPASS_HOSTS = []

# Railway expõe um domínio próprio (algo.up.railway.app) além do domínio
# personalizado configurado — útil manter os dois em ALLOWED_HOSTS durante a
# configuração inicial, antes do domínio próprio estar 100% propagado.
RAILWAY_PUBLIC_DOMAIN = env("RAILWAY_PUBLIC_DOMAIN", default="")  # noqa: F405
if RAILWAY_PUBLIC_DOMAIN and RAILWAY_PUBLIC_DOMAIN not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)  # noqa: F405

# CSRF exige HTTPS + o esquema explícito em cada origem confiável (Django
# não aceita curinga "*", mas aceita "*.dominio" para cobrir os subdomínios
# de cada empresa). Cobre os 4 hosts especiais do middleware de tenant +
# qualquer subdomínio de tenant + domínio próprio de empresa (custom domain
# teria que ser adicionado manualmente aqui se usado — ver apps.tenants.CustomDomain).
CSRF_TRUSTED_ORIGINS = [
    f"https://{TENANT_BASE_DOMAIN}",  # noqa: F405
    f"https://*.{TENANT_BASE_DOMAIN}",  # noqa: F405
    f"https://{PLATFORM_ADMIN_HOST}",
    f"https://{MARKETING_HOST}",  # noqa: F405
    f"https://{CALENDAR_SYNC_HOST}",  # noqa: F405
]
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# WhiteNoise serve os arquivos estáticos direto do processo do Django
# (compactados e com hash no nome do arquivo pra cache "para sempre" no
# navegador) — dispensa um serviço/CDN de estáticos à parte no Railway.
# Precisa vir logo depois do SecurityMiddleware, conforme a documentação do
# WhiteNoise. Mídia (upload de usuário) é outra história — ver STORAGES em
# base.py, que já resolve para S3-compatível quando configurado.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")  # noqa: F405

# Log estruturado (uma linha JSON por evento) — ver apps/core/logging_utils.py.
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405

# Sentry é opcional de propósito: sem SENTRY_DSN configurado (nenhuma conta
# real criada ainda), o app roda normalmente sem monitoramento de erros.
# Quando o DSN existir, é só definir a env var — nenhum código muda.
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),  # noqa: F405
        send_default_pii=False,
        environment=env("ENVIRONMENT", default="production"),  # noqa: F405
    )
