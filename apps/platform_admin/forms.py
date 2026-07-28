from django import forms

from apps.tenants.models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "trade_name", "subdomain", "cnpj", "plan"]
