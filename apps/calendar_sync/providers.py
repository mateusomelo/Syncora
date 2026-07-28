from django.conf import settings

PROVIDER_CONFIGS = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        # access_type=offline + prompt=consent são necessários pro Google
        # devolver um refresh_token (sem isso, só vem access_token de curta
        # duração na primeira autorização).
        "extra_authorize_params": {"access_type": "offline", "prompt": "consent"},
    },
    "outlook": {
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scope": "offline_access Calendars.ReadWrite",
        "client_id": settings.MICROSOFT_OAUTH_CLIENT_ID,
        "client_secret": settings.MICROSOFT_OAUTH_CLIENT_SECRET,
        "extra_authorize_params": {},
    },
}

# Apple Calendar (iCloud) não oferece OAuth2 para apps de terceiros — o
# acesso de verdade é via CalDAV com uma "senha de app" que o usuário gera
# no próprio Apple ID, um mecanismo bem diferente do redirecionamento usado
# para Google/Outlook. Documentado como próximo passo (não implementado)
# em vez de forçar um fluxo OAuth que a Apple não oferece.
UNSUPPORTED_PROVIDERS = {"apple"}


def is_configured(provider):
    config = PROVIDER_CONFIGS.get(provider)
    return bool(config and config["client_id"] and config["client_secret"])
