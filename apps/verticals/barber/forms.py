from django import forms

from apps.clients.models import Client
from apps.services.models import Service

from .models import ClientPackage, Package, Product


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ["name", "services", "session_count", "price", "is_active"]
        widgets = {"services": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ver apps/core/models.py (TenantManager) — queryset precisa ser
        # reatribuído aqui, não herdado do Meta.fields.
        self.fields["services"].queryset = Service.objects.filter(is_active=True)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "stock_quantity", "is_active"]


class SellPackageForm(forms.ModelForm):
    class Meta:
        model = ClientPackage
        fields = ["client", "package"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.all()
        self.fields["package"].queryset = Package.objects.filter(is_active=True)

    def save(self, commit=True):
        self.instance.sessions_remaining = self.instance.package.session_count
        return super().save(commit=commit)
