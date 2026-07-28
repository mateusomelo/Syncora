from rest_framework.throttling import SimpleRateThrottle

# Limite de requisições da API varia pelo plano contratado da empresa, não
# por usuário individual — duas pessoas da mesma empresa dividem a mesma
# cota, o que faz sentido já que a cobrança é por empresa. Ajustável sem
# migração (não depende de campo no banco); se um dia precisar de limites
# customizados por empresa específica, é só promover isso a um campo no
# Plan ou no Tenant.
PLAN_RATES = {
    "basico": "60/min",
    "profissional": "180/min",
    "premium": "600/min",
}
DEFAULT_RATE = "60/min"


class PlanRateThrottle(SimpleRateThrottle):
    scope = "plan"

    def get_rate(self):
        return DEFAULT_RATE

    def allow_request(self, request, view):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            # Sem tenant resolvido (ex.: domínio do Super Admin) — outras
            # permissions (HasTenantMembership) já cobrem esse caso.
            return True

        rate = PLAN_RATES.get(getattr(tenant.plan, "slug", None), DEFAULT_RATE)
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(rate)
        self.key = str(tenant.id)
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.key}
