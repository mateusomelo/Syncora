from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView

from apps.core.views import AdminEmpresaRequiredMixin

from .forms import MembershipInviteForm
from .models import Membership

GENERATED_PASSWORD_SESSION_KEY = "accounts_last_generated_password"


def _is_last_active_admin(membership):
    if membership.role != Membership.Role.ADMIN_EMPRESA or not membership.is_active:
        return False
    return (
        Membership.objects.filter(
            tenant=membership.tenant,
            role=Membership.Role.ADMIN_EMPRESA,
            is_active=True,
        )
        .exclude(pk=membership.pk)
        .count()
        == 0
    )


class MembershipListView(LoginRequiredMixin, AdminEmpresaRequiredMixin, ListView):
    template_name = "accounts/membership_list.html"
    context_object_name = "memberships"

    def get_queryset(self):
        return (
            Membership.objects.filter(tenant=self.request.tenant)
            .select_related("user")
            .order_by("-role", "user__first_name", "user__email")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_choices"] = Membership.Role.choices
        ctx["generated"] = self.request.session.pop(GENERATED_PASSWORD_SESSION_KEY, None)
        return ctx


class MembershipCreateView(LoginRequiredMixin, AdminEmpresaRequiredMixin, FormView):
    form_class = MembershipInviteForm
    template_name = "accounts/membership_form.html"
    success_url = reverse_lazy("accounts:membership_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.tenant
        return kwargs

    def form_valid(self, form):
        membership, generated_password = form.save()
        if generated_password:
            self.request.session[GENERATED_PASSWORD_SESSION_KEY] = {
                "email": membership.user.email,
                "password": generated_password,
            }
        messages.success(self.request, f"{membership.user.email} agora tem acesso à empresa.")
        return redirect(self.success_url)


class MembershipRoleUpdateView(LoginRequiredMixin, AdminEmpresaRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk, tenant=request.tenant)
        new_role = request.POST.get("role")
        if new_role not in Membership.Role.values:
            messages.error(request, "Papel inválido.")
            return redirect("accounts:membership_list")
        if _is_last_active_admin(membership) and new_role != Membership.Role.ADMIN_EMPRESA:
            messages.error(request, "Essa é a única pessoa administradora da empresa — mude o papel de outra pessoa primeiro.")
            return redirect("accounts:membership_list")
        membership.role = new_role
        membership.save(update_fields=["role"])
        messages.success(request, f"Papel de {membership.user.email} atualizado.")
        return redirect("accounts:membership_list")


class MembershipToggleActiveView(LoginRequiredMixin, AdminEmpresaRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk, tenant=request.tenant)
        if membership.is_active and _is_last_active_admin(membership):
            messages.error(request, "Essa é a única pessoa administradora ativa da empresa — não é possível desativá-la.")
            return redirect("accounts:membership_list")
        membership.is_active = not membership.is_active
        membership.save(update_fields=["is_active"])
        messages.success(
            request,
            f"{membership.user.email} foi {'reativado' if membership.is_active else 'desativado'}.",
        )
        return redirect("accounts:membership_list")


class MembershipDeleteView(LoginRequiredMixin, AdminEmpresaRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk, tenant=request.tenant)
        if _is_last_active_admin(membership):
            messages.error(request, "Essa é a única pessoa administradora ativa da empresa — não é possível removê-la.")
            return redirect("accounts:membership_list")
        email = membership.user.email
        membership.delete()
        messages.success(request, f"{email} não tem mais acesso à empresa.")
        return redirect("accounts:membership_list")
