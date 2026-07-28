from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.core.views import TenantRequiredMixin
from apps.staff.models import Professional
from apps.tenants.models import Tenant

from .models import CalendarConnection
from .providers import PROVIDER_CONFIGS, UNSUPPORTED_PROVIDERS, is_configured

STATE_SALT = "calendar_sync.oauth_state"
STATE_MAX_AGE = 600  # 10 minutos pra completar o fluxo de consentimento


class ProfessionalCalendarView(LoginRequiredMixin, TenantRequiredMixin, ListView):
    """Tela de conexões de calendário de um profissional: botões conectar/
    desconectar Google/Outlook e a direção de sincronização de cada um."""

    template_name = "calendar_sync/professional_calendar.html"
    context_object_name = "connections"

    def get_queryset(self):
        self.professional = get_object_or_404(Professional, pk=self.kwargs["professional_pk"])
        return CalendarConnection.objects.filter(professional=self.professional)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["professional"] = self.professional
        ctx["provider_options"] = [
            {
                "key": key,
                "label": CalendarConnection.Provider(key).label,
                "configured": is_configured(key),
            }
            for key in ["google", "outlook"]
        ]
        ctx["sync_status"] = self.request.GET.get("sync_status")
        return ctx


class CalendarConnectView(LoginRequiredMixin, TenantRequiredMixin, View):
    """Inicia o fluxo OAuth: monta o state assinado (empresa + profissional +
    de onde veio) e redireciona para a tela de consentimento do provedor."""

    def get(self, request, professional_pk, provider):
        professional = get_object_or_404(Professional, pk=professional_pk)
        return_path = f"/app/profissionais/{professional.id}/calendario/"

        if provider in UNSUPPORTED_PROVIDERS:
            messages.error(
                request,
                "Apple Calendar ainda não está disponível — usa um mecanismo diferente (CalDAV), não OAuth.",
            )
            return redirect(return_path)

        config = PROVIDER_CONFIGS.get(provider)
        if not config or not is_configured(provider):
            messages.error(
                request,
                f"Integração com {provider} ainda não foi configurada pelo administrador da plataforma "
                "(faltam as credenciais OAuth).",
            )
            return redirect(return_path)

        state = signing.dumps(
            {
                "tenant_id": str(request.tenant.id),
                "professional_id": professional.id,
                "provider": provider,
                # Captura a origem exata (esquema+host+porta) de onde o
                # usuário clicou, pra saber pra onde voltar depois do
                # provedor redirecionar pro CALENDAR_SYNC_HOST fixo.
                "return_origin": f"{request.scheme}://{request.get_host()}",
            },
            salt=STATE_SALT,
        )
        redirect_uri = f"{settings.CALENDAR_SYNC_CALLBACK_BASE_URL}/calendar-sync/{provider}/callback/"
        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scope"],
            "state": state,
            **config["extra_authorize_params"],
        }
        return redirect(f"{config['authorize_url']}?{urlencode(params)}")


class CalendarCallbackView(View):
    """Roda no CALENDAR_SYNC_HOST, fora de qualquer tenant (ver
    TenantResolutionMiddleware). Troca o code pelos tokens, decodifica o
    state assinado pra achar a empresa/profissional certos, salva a conexão
    e redireciona de volta pro subdomínio de onde o usuário veio."""

    def get(self, request, provider):
        state_raw = request.GET.get("state", "")
        try:
            state = signing.loads(state_raw, salt=STATE_SALT, max_age=STATE_MAX_AGE)
        except signing.BadSignature:
            return HttpResponseBadRequest("State inválido ou expirado — tente conectar de novo.")

        return_origin = state["return_origin"]
        return_path = f"/app/profissionais/{state['professional_id']}/calendario/"

        if request.GET.get("error"):
            return redirect(f"{return_origin}{return_path}?sync_status=error&reason=consent_denied")

        config = PROVIDER_CONFIGS.get(provider)
        if not config:
            return redirect(f"{return_origin}{return_path}?sync_status=error&reason=unknown_provider")

        tenant = get_object_or_404(Tenant, pk=state["tenant_id"])
        professional = get_object_or_404(
            Professional.all_objects, pk=state["professional_id"], tenant=tenant
        )

        token_response = requests.post(
            config["token_url"],
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": request.GET.get("code", ""),
                "redirect_uri": f"{settings.CALENDAR_SYNC_CALLBACK_BASE_URL}/calendar-sync/{provider}/callback/",
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if token_response.status_code != 200:
            return redirect(f"{return_origin}{return_path}?sync_status=error&reason=token_exchange_failed")

        payload = token_response.json()
        expires_in = payload.get("expires_in", 3600)

        # Fora de qualquer request de tenant (contextvar vazio) — precisa de
        # all_objects, senão o TenantManager nunca encontra a conexão
        # existente e update_or_create tenta inserir de novo a cada conexão,
        # colidindo com a unique_together (ver apps/core/models.py).
        CalendarConnection.all_objects.update_or_create(
            professional=professional,
            provider=provider,
            defaults={
                "tenant": tenant,
                "access_token": payload.get("access_token", ""),
                "refresh_token": payload.get("refresh_token", ""),
                "token_expires_at": timezone.now() + timedelta(seconds=expires_in),
                "is_active": True,
            },
        )
        return redirect(f"{return_origin}{return_path}?sync_status=connected&provider={provider}")


class CalendarDisconnectView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, professional_pk, pk):
        connection = get_object_or_404(CalendarConnection, pk=pk, professional_id=professional_pk)
        connection.delete()  # soft delete
        messages.success(request, f"{connection.get_provider_display()} desconectado.")
        return redirect("calendar_sync:professional_calendar", professional_pk=professional_pk)


class CalendarSyncDirectionView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, professional_pk, pk):
        connection = get_object_or_404(CalendarConnection, pk=pk, professional_id=professional_pk)
        direction = request.POST.get("sync_direction")
        if direction in CalendarConnection.SyncDirection.values:
            connection.sync_direction = direction
            connection.save(update_fields=["sync_direction"])
        return redirect("calendar_sync:professional_calendar", professional_pk=professional_pk)
