from django import forms

from .models import Tenant


class TenantSelfServiceForm(forms.ModelForm):
    """Campos que a própria empresa pode editar. Subdomínio, status e plano
    ficam de fora -- só o Super Admin mexe nisso (platform_admin.TenantForm)."""

    class Meta:
        model = Tenant
        fields = ["name", "trade_name", "cnpj"]
        labels = {
            "name": "Razão social",
            "trade_name": "Nome fantasia",
            "cnpj": "CNPJ",
        }
