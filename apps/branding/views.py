from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.core.views import AdminEmpresaRequiredMixin
from apps.verticals.registry import VERTICALS, get_active_verticals

from .forms import BrandingSettingsForm
from .models import BrandingSettings


class BrandingSettingsView(LoginRequiredMixin, AdminEmpresaRequiredMixin, UpdateView):
    model = BrandingSettings
    form_class = BrandingSettingsForm
    template_name = "branding/settings.html"
    success_url = reverse_lazy("branding:settings")

    def get_object(self, queryset=None):
        settings, _created = BrandingSettings.objects.get_or_create(tenant=self.request.tenant)
        return settings

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        active = get_active_verticals(self.request.tenant)
        ctx["active_vertical_label"] = VERTICALS[active[0]]["label"] if active else "Padrão"
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Aparência atualizada.")
        return redirect(self.success_url)
