from .base import *  # noqa: F401,F403

DEBUG = False

# Host usado pelo Django test Client / pytest-django por padrão.
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
TENANT_BYPASS_HOSTS = ["testserver", "localhost", "127.0.0.1"]

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

AXES_ENABLED = False

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
