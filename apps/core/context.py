"""Contexto do tenant corrente, seguro para código sync e async (contextvars).

Populado pelo TenantResolutionMiddleware (apps.tenants) a cada request, a
partir do Host header. Nunca importar apps.tenants aqui — isolamento
proposital para evitar import circular (tenants -> core -> tenants).
"""

from contextvars import ContextVar

_current_tenant_id: ContextVar[object | None] = ContextVar(
    "current_tenant_id", default=None
)


def get_current_tenant_id():
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id):
    return _current_tenant_id.set(tenant_id)


def reset_current_tenant_id(token):
    _current_tenant_id.reset(token)
