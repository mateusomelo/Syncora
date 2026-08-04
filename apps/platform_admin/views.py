from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from apps.accounts.forms import MembershipInviteForm, generate_password
from apps.accounts.models import Membership, User
from apps.accounts.views import _is_last_active_admin
from apps.audit.models import AuditLog, ImpersonationSession
from apps.branding.models import BrandingSettings
from apps.scheduling.models import Appointment
from apps.tenants.models import FeatureFlag, Tenant
from apps.verticals.barber.models import ClientPackage
from apps.verticals.psychology.models import ClinicalRecord
from apps.verticals.registry import VERTICALS

from .forms import PlatformAdminInviteForm, TenantCreateForm, TenantForm


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
        qs = Tenant.all_objects.select_related("plan").order_by("name")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(subdomain__icontains=query) | Q(trade_name__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_tenants = Tenant.all_objects.select_related("plan").all()
        ctx["query"] = self.request.GET.get("q", "")
        ctx["stats"] = {
            "total": all_tenants.count(),
            "active": all_tenants.filter(status=Tenant.Status.ACTIVE).count(),
            "trial": all_tenants.filter(status=Tenant.Status.TRIAL).count(),
            "suspended": all_tenants.filter(status=Tenant.Status.SUSPENDED).count(),
            "mrr": sum((t.plan.price for t in all_tenants if t.status == Tenant.Status.ACTIVE), start=0),
        }
        return ctx


class TenantCreateView(PlatformAdminRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantCreateForm
    template_name = "platform_admin/tenant_form.html"
    success_url = reverse_lazy("platform_admin:tenant_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        tenant = self.object
        BrandingSettings.objects.get_or_create(tenant=tenant)

        segment = form.cleaned_data["segment"]
        FeatureFlag.objects.create(tenant=tenant, key=VERTICALS[segment]["flag_key"], enabled=True)

        password = form.cleaned_data["admin_password"] or generate_password()
        admin_user = User.objects.create_user(email=form.cleaned_data["admin_email"], password=password)
        Membership.objects.create(user=admin_user, tenant=tenant, role=Membership.Role.ADMIN_EMPRESA)

        _log(
            self.request,
            "tenant.create",
            tenant,
            changes={"segment": segment, "admin_email": admin_user.email},
        )
        if not form.cleaned_data["admin_password"]:
            messages.success(
                self.request,
                format_html(
                    '"{}" criada! Acesso do admin: <strong>{}</strong> — senha inicial: <code>{}</code> (copie agora, não aparece de novo).',
                    tenant.name,
                    admin_user.email,
                    password,
                ),
            )
        else:
            messages.success(self.request, f'"{tenant.name}" criada com acesso para {admin_user.email}.')
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
        ctx["memberships"] = Membership.objects.filter(tenant=self.object).select_related(
            "user"
        ).order_by("-role", "user__email")
        ctx["membership_form"] = MembershipInviteForm(tenant=self.object)
        ctx["role_choices"] = Membership.Role.choices
        return ctx


class TenantUserCreateView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        form = MembershipInviteForm(request.POST, tenant=tenant)
        if not form.is_valid():
            errors = " ".join(f"{f}: {', '.join(e)}" for f, e in form.errors.items())
            messages.error(request, f"Não deu pra criar o acesso — {errors}")
            return redirect("platform_admin:tenant_detail", pk=pk)

        membership, generated_password = form.save()
        _log(
            request,
            "tenant.user.create",
            tenant,
            changes={"email": membership.user.email, "role": membership.role},
        )
        if generated_password:
            messages.success(
                request,
                format_html(
                    "Acesso criado para <strong>{}</strong>. Senha inicial: <code>{}</code> — copie agora, não aparece de novo.",
                    membership.user.email,
                    generated_password,
                ),
            )
        else:
            messages.success(request, f"{membership.user.email} agora tem acesso a {tenant.name}.")
        return redirect("platform_admin:tenant_detail", pk=pk)


class TenantUserRoleUpdateView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        membership = get_object_or_404(Membership, pk=membership_pk, tenant=tenant)
        new_role = request.POST.get("role")
        if new_role not in Membership.Role.values:
            messages.error(request, "Papel inválido.")
            return redirect("platform_admin:tenant_detail", pk=pk)
        if _is_last_active_admin(membership) and new_role != Membership.Role.ADMIN_EMPRESA:
            messages.error(request, "Essa é a única pessoa administradora da empresa — mude o papel de outra pessoa primeiro.")
            return redirect("platform_admin:tenant_detail", pk=pk)
        membership.role = new_role
        membership.save(update_fields=["role"])
        _log(request, "tenant.user.role_update", tenant, changes={"email": membership.user.email, "role": new_role})
        messages.success(request, f"Papel de {membership.user.email} atualizado.")
        return redirect("platform_admin:tenant_detail", pk=pk)


class TenantUserToggleActiveView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        membership = get_object_or_404(Membership, pk=membership_pk, tenant=tenant)
        if membership.is_active and _is_last_active_admin(membership):
            messages.error(request, "Essa é a única pessoa administradora ativa da empresa — não é possível desativá-la.")
            return redirect("platform_admin:tenant_detail", pk=pk)
        membership.is_active = not membership.is_active
        membership.save(update_fields=["is_active"])
        _log(
            request,
            "tenant.user.toggle_active",
            tenant,
            changes={"email": membership.user.email, "is_active": membership.is_active},
        )
        messages.success(
            request,
            f"{membership.user.email} foi {'reativado' if membership.is_active else 'desativado'}.",
        )
        return redirect("platform_admin:tenant_detail", pk=pk)


class TenantUserDeleteView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk, membership_pk):
        tenant = get_object_or_404(Tenant.all_objects, pk=pk)
        membership = get_object_or_404(Membership, pk=membership_pk, tenant=tenant)
        if _is_last_active_admin(membership):
            messages.error(request, "Essa é a única pessoa administradora ativa da empresa — não é possível removê-la.")
            return redirect("platform_admin:tenant_detail", pk=pk)
        email = membership.user.email
        membership.delete()
        _log(request, "tenant.user.remove", tenant, changes={"email": email})
        messages.success(request, f"{email} não tem mais acesso à empresa.")
        return redirect("platform_admin:tenant_detail", pk=pk)


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


class PlatformAdminUserListView(PlatformAdminRequiredMixin, ListView):
    template_name = "platform_admin/admin_user_list.html"
    context_object_name = "admins"

    def get_queryset(self):
        return User.objects.filter(is_platform_admin=True).order_by("first_name", "email")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["invite_form"] = PlatformAdminInviteForm()
        ctx["generated"] = self.request.session.pop("platform_admin_generated_password", None)
        return ctx


class PlatformAdminUserCreateView(PlatformAdminRequiredMixin, FormView):
    form_class = PlatformAdminInviteForm
    template_name = "platform_admin/admin_user_list.html"
    success_url = reverse_lazy("platform_admin:admin_user_list")

    def form_invalid(self, form):
        errors = " ".join(f"{f}: {', '.join(e)}" for f, e in form.errors.items())
        messages.error(self.request, f"Não deu pra criar o acesso — {errors}")
        return redirect(self.success_url)

    def form_valid(self, form):
        user, password = form.save()
        _log(self.request, "platform_admin.create", None, changes={"email": user.email})
        self.request.session["platform_admin_generated_password"] = {
            "email": user.email,
            "password": password,
        }
        messages.success(self.request, f"{user.email} agora é Super Admin.")
        return redirect(self.success_url)


class PlatformAdminUserRevokeView(PlatformAdminRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk, is_platform_admin=True)
        if target.pk == request.user.pk:
            messages.error(request, "Você não pode revogar o próprio acesso.")
            return redirect("platform_admin:admin_user_list")
        if User.objects.filter(is_platform_admin=True).exclude(pk=target.pk).count() == 0:
            messages.error(request, "Essa é a única conta de Super Admin — não é possível revogar.")
            return redirect("platform_admin:admin_user_list")
        target.is_platform_admin = False
        target.save(update_fields=["is_platform_admin"])
        _log(request, "platform_admin.revoke", None, changes={"email": target.email})
        messages.success(request, f"Acesso de Super Admin de {target.email} revogado.")
        return redirect("platform_admin:admin_user_list")
