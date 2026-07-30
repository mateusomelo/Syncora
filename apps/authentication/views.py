from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Membership

from .serializers import TenantTokenObtainPairSerializer


class TenantTokenObtainPairView(TokenObtainPairView):
    serializer_class = TenantTokenObtainPairSerializer


class LoginView(auth_views.LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Sem domínio próprio ainda, o login sempre acontece no mesmo
        endereço (não por subdomínio) -- então depois de autenticar,
        decidimos aqui pra qual empresa mandar: direto se só tiver uma,
        ou pra tela de escolha (ChooseTenantView) se tiver mais de uma.
        Quando `request.tenant` já veio resolvido (subdomínio/domínio
        próprio de verdade), não há o que escolher -- segue direto."""
        user = form.get_user()
        auth_login(self.request, user)

        if user.is_platform_admin or self.request.tenant is not None:
            return HttpResponseRedirect(self.get_success_url())

        memberships = list(
            Membership.objects.filter(user=user, is_active=True).select_related("tenant")
        )
        if len(memberships) == 1:
            self.request.session["active_tenant_id"] = str(memberships[0].tenant_id)
        elif len(memberships) > 1:
            return HttpResponseRedirect(reverse("authentication:choose_tenant"))

        return HttpResponseRedirect(self.get_success_url())


class ChooseTenantView(LoginRequiredMixin, TemplateView):
    """Tela pra escolher qual empresa acessar -- usada logo após o login
    quando o usuário tem mais de uma Membership ativa, e também disponível
    a qualquer momento pra trocar de empresa (ver app_shell.html)."""

    template_name = "auth/choose_tenant.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["memberships"] = Membership.objects.filter(
            user=self.request.user, is_active=True
        ).select_related("tenant")
        return ctx

    def post(self, request, *args, **kwargs):
        membership = Membership.objects.filter(
            pk=request.POST.get("membership_id"), user=request.user, is_active=True
        ).first()
        if membership is not None:
            request.session["active_tenant_id"] = str(membership.tenant_id)
            return HttpResponseRedirect(reverse("dashboard:home"))
        return HttpResponseRedirect(reverse("authentication:choose_tenant"))


class LogoutView(auth_views.LogoutView):
    pass


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "auth/password_reset_form.html"
    email_template_name = "emails/password_reset_email.html"
    subject_template_name = "emails/password_reset_subject.txt"
    success_url = reverse_lazy("authentication:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("authentication:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "auth/password_reset_complete.html"
