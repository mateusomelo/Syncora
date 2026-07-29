from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.audit.models import AuditLog, ImpersonationSession
from apps.branding.models import BrandingSettings
from apps.scheduling.models import Appointment
from apps.tenants.models import FeatureFlag, Tenant
from apps.verticals.barber.models import ClientPackage
from apps.verticals.psychology.models import ClinicalRecord

from .forms import TenantForm


def _jsonable(data):
    return {key: str(value) for key, value in data.items()}


def _log(request, action, tenant, changes=None, is_impersonated=False):
    AuditLog.objects.create(
        tenant=tenant,
        actor=request.user,
        action=action,
        target_model="Tenant",
        target_id=str(tenant.id) if tenant else "",
        changes=changes or {},
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        is_impersonated=is_impersonated,
    )


class PlatformAdminRequiredMixin(UserPassesTestMixin):
    login_url = "authentication:login"

    def test_func(self):
        user = self.request.user
        return bool(user.is_authenticated and user.is_platform_admin)


class TenantListView(PlatformAdminRequiredMixin, ListView):
    template_name = "platform_admin/tenant_list.html"
    context_object_name = "tenants"
    paginate_by = 25

    def get_queryset(self):
        return Tenant.all_objects.select_related("plan").order_by("name")


class TenantCreateView(PlatformAdminRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = "platform_admin/tenant_form.html"
    success_url = reverse_lazy("platform_admin:tenant_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        BrandingSettings.objects.get_or_create(tenant=self.object)
        _log(self.request, "tenant.create", self.object)
        return response


class TenantUpdateView(PlatformAdminRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = "platform_admin/tenant_form.html"
    success_url = reverse_lazy("platform_admin:tenant_list")
    queryset = Tenant.all_objects.all()

    def form_valid(self, form):
        changes = {field: form.cleaned_data[field] for field in form.changed_data}
        response = super().form_valid(form)
        _log(self.request, "tenant.update", self.object, changes=_jsonable(changes))
        return response


class TenantDetailView(PlatformAdminRequiredMixin, DetailView):
    template_name = "platform_admin/tenant_detail.html"
    context_object_name = "tenant"
    queryset = Tenant.all_objects.select_related("plan").prefetch_related(
        "feature_flags", "custom_domains"
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        existing = {flag.key: flag for flag in self.object.feature_flags.all()}
        ctx["feature_flags"] = [
            (key, label, existing.get(key)) for key, label in FeatureFlag.Key.choices
        ]
        ctx["active_impersonation"] = ImpersonationSession.objects.filter(
            tenant=self.object, ended_at__isnull=True
        ).first()
        return ctx


class TenantSuspendView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        tenant.status = Tenant.Status.SUSPENDED
        tenant.suspended_reason = request.POST.get("reason", "")
        tenant.save(update_fields=["status", "suspended_reason"])
        _log(request, "tenant.suspend", tenant, changes={"reason": tenant.suspended_reason})
        messages.success(request, f"{tenant.name} suspensa.")
        return redirect("platform_admin:tenant_detail", pk=pk)


class TenantActivateView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        tenant.status = Tenant.Status.ACTIVE
        tenant.suspended_reason = ""
        tenant.save(update_fields=["status", "suspended_reason"])
        _log(request, "tenant.activate", tenant)
        messages.success(request, f"{tenant.name} ativada.")
        return redirect("platform_admin:tenant_detail", pk=pk)


class TenantDeleteView(PlatformAdminRequiredMixin, View):
    """Exclusão permanente (não é o soft-delete padrão). Exige digitar o
    subdomínio de volta pra confirmar — irreversível, sem lixeira.

    Appointment/ClinicalRecord/ClientPackage usam on_delete=PROTECT em cima
    de Client/Professional/Package (histórico não deve sumir sozinho num
    cascade) — isso bloqueia até o cascade automático do Tenant se esses
    registros ainda existirem. Por isso são apagados explicitamente aqui
    antes do hard_delete() do tenant, na ordem certa. Mesmo padrão usado
    nos scripts de smoke test a sessão inteira (ver docs/memória do projeto)."""

    def post(self, request, pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        if request.POST.get("confirm_subdomain", "").strip() != tenant.subdomain:
            messages.error(request, "Subdomínio não confere — exclusão cancelada.")
            return redirect("platform_admin:tenant_detail", pk=pk)

        name = tenant.name
        _log(request, "tenant.delete", tenant, changes={"subdomain": tenant.subdomain})

        Appointment.all_objects.filter(tenant=tenant).hard_delete()
        ClinicalRecord.all_objects.filter(tenant=tenant).hard_delete()
        ClientPackage.all_objects.filter(tenant=tenant).hard_delete()
        tenant.delete(hard=True)

        messages.success(request, f'"{name}" foi excluída permanentemente.')
        return redirect("platform_admin:tenant_list")


class FeatureFlagToggleView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk, key):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        flag, _created = FeatureFlag.objects.get_or_create(tenant=tenant, key=key)
        flag.enabled = not flag.enabled
        flag.save(update_fields=["enabled"])
        _log(
            request,
            "tenant.feature_flag.toggle",
            tenant,
            changes={"key": key, "enabled": flag.enabled},
        )
        return redirect("platform_admin:tenant_detail", pk=pk)


class ImpersonationStartView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        session = ImpersonationSession.objects.create(
            super_admin=request.user,
            tenant=tenant,
            reason=request.POST.get("reason", ""),
        )
        request.session["impersonating_tenant_id"] = str(tenant.id)
        request.session["impersonation_session_id"] = session.id
        _log(request, "impersonation.start", tenant, is_impersonated=True)
        return redirect("dashboard:home")


class ImpersonationStopView(PlatformAdminRequiredMixin, View):
    def post(self, request):
        session_id = request.session.pop("impersonation_session_id", None)
        tenant_id = request.session.pop("impersonating_tenant_id", None)
        tenant = Tenant.all_objects.filter(pk=tenant_id).first() if tenant_id else None
        if session_id:
            ImpersonationSession.objects.filter(
                pk=session_id, ended_at__isnull=True
            ).update(ended_at=timezone.now())
        _log(request, "impersonation.stop", tenant, is_impersonated=True)
        messages.info(request, "Você saiu do modo de suporte.")
        return redirect("platform_admin:tenant_list")


class ImpersonationActiveView(PlatformAdminRequiredMixin, TemplateView):
    template_name = "platform_admin/impersonation_active.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenant"] = self.request.tenant
        return ctx
