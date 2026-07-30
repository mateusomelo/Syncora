from django import forms

from apps.tenants.models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "trade_name", "subdomain", "cnpj", "plan"]
        labels = {
            "name": "Razão social",
            "trade_name": "Nome fantasia",
            "subdomain": "Subdomínio",
            "cnpj": "CNPJ",
            "plan": "Plano",
        }
