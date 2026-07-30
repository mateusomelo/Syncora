from django.conf import settings
from django.core.cache import cache
from django.http import Http404

from apps.core.context import reset_current_tenant_id, set_current_tenant_id

from .models import CustomDomain, Tenant

CACHE_TTL_SECONDS = 30
_NONE_SENTINEL = "__none__"


def invalidate_tenant_cache(tenant):
    """Limpa o cache de resolução de host pro subdomínio (e domínios
    próprios) desse tenant -- chamado pelos signals em apps/tenants/signals.py
    sempre que o Tenant ou um CustomDomain dele muda. Sem isso, editar dados
    da empresa (ou suspendê-la!) podia levar até CACHE_TTL_SECONDS pra
    refletir, porque o middleware reaproveitava o objeto Tenant cacheado.

    A chave precisa ser o host completo (subdomínio + TENANT_BASE_DOMAIN),
    igual ao que _resolve_tenant() usa -- não só o subdomínio sozinho."""
    cache.delete(f"tenant_resolution:{tenant.subdomain}.{settings.TENANT_BASE_DOMAIN}")
    for domain in tenant.custom_domains.all():
        cache.delete(f"tenant_resolution:{domain.domain}")


class TenantResolutionMiddleware:
    """Resolve o tenant pelo Host header antes de qualquer outra lógica de
    request e injeta em request.tenant + contextvar (lido pelo TenantManager
    em apps.core.models). Roda antes da autenticação.

    Quatro hosts escapam da resolução de tenant por design:
    - PLATFORM_ADMIN_HOST: área do Super Admin, cross-tenant por natureza.
    - CALENDAR_SYNC_HOST: callback fixo de OAuth (Google/Outlook exigem um
      redirect_uri cadastrado antecipadamente, não dá pra usar o
      subdomínio de cada empresa) — ver apps/calendar_sync.
    - MARKETING_HOST: site público/cadastro self-service (apps/onboarding)
      — antes de existir tenant nenhum, óbvio que não há tenant a resolver.
    - TENANT_BYPASS_HOSTS: conveniência de desenvolvimento local
      (localhost/127.0.0.1) — deve ficar vazio em produção.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()

        if host == settings.CALENDAR_SYNC_HOST:
            request.tenant = None
            request.is_impersonating = False
            return self.get_response(request)

        is_admin_host = (
            host == settings.PLATFORM_ADMIN_HOST
            or host == settings.MARKETING_HOST
            or host in settings.TENANT_BYPASS_HOSTS
        )

        if is_admin_host:
            # No domínio administrativo (ou bypass local, ou o único domínio
            # real disponível antes de comprar um domínio próprio), o tenant
            # só vem da sessão: ou uma impersonação de Super Admin (banner
            # "atuando como suporte"), ou a empresa que o próprio usuário
            # escolheu no login (sem banner nenhum -- é o uso normal dele,
            # só que sem subdomínio próprio ainda). Ver
            # apps/authentication/views.py:LoginView/ChooseTenantView.
            tenant, is_impersonating = self._resolve_session_tenant(request)
        else:
            tenant = self._resolve_tenant(host)
            if tenant is None or not tenant.is_operational:
                raise Http404("Empresa não encontrada ou inativa para este domínio.")
            is_impersonating = False

        request.tenant = tenant
        request.is_impersonating = is_impersonating

        if tenant is None:
            return self.get_response(request)

        token = set_current_tenant_id(tenant.id)
        try:
            return self.get_response(request)
        finally:
            reset_current_tenant_id(token)

    def _resolve_session_tenant(self, request):
        impersonating_id = request.session.get("impersonating_tenant_id")
        if impersonating_id:
            # Suporte pode acessar mesmo uma empresa suspensa (é o cenário
            # mais comum de precisar impersonar), por isso sem checar
            # is_operational aqui -- diferente do active_tenant_id abaixo.
            tenant = Tenant.objects.filter(id=impersonating_id).first()
            if tenant is not None:
                return tenant, True

        active_id = request.session.get("active_tenant_id")
        if active_id:
            tenant = Tenant.objects.filter(id=active_id).first()
            if tenant is not None and tenant.is_operational:
                return tenant, False

        return None, False

    def _resolve_tenant(self, host):
        cache_key = f"tenant_resolution:{host}"
        cached = cache.get(cache_key)
        if cached is not None:
            return None if cached == _NONE_SENTINEL else cached

        tenant = self._resolve_by_subdomain(host) or self._resolve_by_custom_domain(host)
        cache.set(cache_key, tenant or _NONE_SENTINEL, CACHE_TTL_SECONDS)
        return tenant

    def _resolve_by_subdomain(self, host):
        base_domain = settings.TENANT_BASE_DOMAIN
        suffix = f".{base_domain}"
        if not host.endswith(suffix):
            return None
        subdomain = host[: -len(suffix)]
        return Tenant.objects.filter(subdomain=subdomain).first()

    def _resolve_by_custom_domain(self, host):
        domain = (
            CustomDomain.objects.select_related("tenant")
            .filter(domain=host, verified_at__isnull=False)
            .first()
        )
        return domain.tenant if domain else None
