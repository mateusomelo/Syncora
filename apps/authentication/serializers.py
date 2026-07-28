from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adiciona tenant_id, role e is_platform_admin como claims do access
    token — evita um hit de DB extra em toda request autenticada da API
    só para descobrir em qual tenant/papel o usuário está agindo."""

    def validate(self, attrs):
        data = super().validate(attrs)

        request = self.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None

        role = None
        if tenant is not None:
            membership = self.user.memberships.filter(
                tenant=tenant, is_active=True
            ).first()
            role = membership.role if membership else None

        access = self.get_token(self.user).access_token
        access["tenant_id"] = str(tenant.id) if tenant else None
        access["role"] = role
        access["is_platform_admin"] = self.user.is_platform_admin
        data["access"] = str(access)
        return data
