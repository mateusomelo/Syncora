from .base import *  # noqa: F401,F403

DEBUG = False

TENANT_BASE_DOMAIN = env("TENANT_BASE_DOMAIN", default="syncora.app")  # noqa: F405
PLATFORM_ADMIN_HOST = env("PLATFORM_ADMIN_HOST", default="admin.syncora.app")  # noqa: F405
# Em produção, todo host precisa resolver para um tenant real ou para o
# domínio administrativo — nenhum atalho de conveniência.
TENANT_BYPASS_HOSTS = []

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
