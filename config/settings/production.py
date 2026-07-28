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
