from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone


class IdleSessionTimeoutMiddleware:
    """Desloga de verdade depois de settings.SESSION_IDLE_TIMEOUT_SECONDS sem
    nenhuma request autenticada. Sem isso, o cookie de sessão "rolante" padrão
    do Django (cada save recalcula o vencimento pra daqui a SESSION_COOKIE_AGE)
    nunca expira de fato pra quem visita o site com alguma frequência --
    exatamente o bug relatado (sessão viva depois de uma semana parada)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get("last_activity")
            now = timezone.now().timestamp()
            if last_activity is not None and now - last_activity > settings.SESSION_IDLE_TIMEOUT_SECONDS:
                logout(request)
                messages.info(request, "Sua sessão expirou por inatividade. Faça login novamente.")
            else:
                request.session["last_activity"] = now
        return self.get_response(request)
