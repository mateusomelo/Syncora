from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.core.views import AdminEmpresaRequiredMixin

from .forms import TenantSelfServiceForm
from .models import Tenant


class TenantSettingsView(LoginRequiredMixin, AdminEmpresaRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantSelfServiceForm
    template_name = "tenants/company_settings.html"
    success_url = reverse_lazy("tenants:settings")

    def get_object(self, queryset=None):
        return self.request.tenant

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Dados da empresa atualizados.")
        return redirect(self.success_url)
