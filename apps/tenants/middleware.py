from django.conf import settings
from django.core.cache import cache
from django.http import Http404

from apps.core.context import reset_current_tenant_id, set_current_tenant_id

from .models import CustomDomain, Tenant

CACHE_TTL_SECONDS = 30
_NONE_SENTINEL = "__none__"


class TenantResolutionMiddleware:
    """Resolve o tenant pelo Host header antes de qualquer outra lógica de
    request e injeta em request.tenant + contextvar (lido pelo TenantManager
    em apps.core.models). Roda antes da autenticação.

    Dois hosts escapam da resolução de tenant por design:
    - PLATFORM_ADMIN_HOST: área do Super Admin, cross-tenant por natureza.
    - TENANT_BYPASS_HOSTS: conveniência de desenvolvimento local
      (localhost/127.0.0.1) — deve ficar vazio em produção.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()

        if host == settings.PLATFORM_ADMIN_HOST or host in settings.TENANT_BYPASS_HOSTS:
            request.tenant = None
            return self.get_response(request)

        tenant = self._resolve_tenant(host)
        if tenant is None or not tenant.is_operational:
            raise Http404("Empresa não encontrada ou inativa para este domínio.")

        request.tenant = tenant
        token = set_current_tenant_id(tenant.id)
        try:
            response = self.get_response(request)
        finally:
            reset_current_tenant_id(token)
        return response

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
