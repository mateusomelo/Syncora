from rest_framework.permissions import BasePermission


class HasTenantMembership(BasePermission):
    """Garante que o usuário autenticado (via JWT ou sessão) tem vínculo
    ativo com o tenant resolvido pela request.

    JWTAuthentication não passa pelo TenantAwareBackend (apps/accounts/
    backends.py) — esse backend só roda no login por sessão/formulário.
    Sem esta permission, um token JWT válido de um usuário da empresa A
    seria aceito em qualquer subdomínio, inclusive o da empresa B, já que
    JWTAuthentication só valida a assinatura do token e busca o User, sem
    checar Membership nenhuma. Esta classe fecha esse buraco."""

    message = "Você não tem vínculo ativo com esta empresa."

    def has_permission(self, request, view):
        from apps.accounts.models import Membership

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return bool(request.user and request.user.is_platform_admin)
        return Membership.objects.filter(
            user=request.user, tenant=tenant, is_active=True
        ).exists()
