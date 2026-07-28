from django.contrib.auth.backends import ModelBackend

from .models import Membership


class TenantAwareBackend(ModelBackend):
    """Autentica por e-mail/senha e, quando a request está associada a um
    tenant (request.tenant setado pelo TenantResolutionMiddleware), exige uma
    Membership ativa nesse tenant. Super admins (is_platform_admin) só
    autenticam fora de contexto de tenant (área administrativa do Syncora).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(
            request, username=username, password=password, **kwargs
        )
        if user is None:
            return None

        tenant = getattr(request, "tenant", None) if request else None

        if tenant is None:
            return user if user.is_platform_admin else None

        has_active_membership = Membership.objects.filter(
            user=user, tenant=tenant, is_active=True
        ).exists()
        return user if has_active_membership else None
