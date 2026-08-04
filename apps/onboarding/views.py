from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView

from apps.accounts.models import Membership, User
from apps.branding.models import BrandingSettings
from apps.tenants.models import FeatureFlag, Tenant
from apps.verticals.registry import VERTICALS

from .forms import SignupForm


class SignupView(FormView):
    form_class = SignupForm
    template_name = "onboarding/signup.html"

    def form_valid(self, form):
        data = form.cleaned_data
        coupon = data.get("coupon_code")

        with transaction.atomic():
            tenant = Tenant.objects.create(
                name=data["company_name"],
                subdomain=data["subdomain"],
                plan=data["plan"],
                status=Tenant.Status.TRIAL,
            )
            BrandingSettings.objects.create(tenant=tenant)
            FeatureFlag.objects.create(
                tenant=tenant, key=VERTICALS[data["segment"]]["flag_key"], enabled=True
            )
            user = User.objects.create_user(
                email=data["admin_email"], password=data["admin_password"]
            )
            Membership.objects.create(user=user, tenant=tenant, role=Membership.Role.ADMIN_EMPRESA)
            if coupon:
                coupon.times_used += 1
                coupon.save(update_fields=["times_used"])

        send_mail(
            "Bem-vindo ao Syncora!",
            render_to_string("onboarding/welcome_email.txt", {"tenant": tenant}),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        # Sem domínio próprio configurado, não há subdomínio de verdade pra
        # mandar a pessoa acessar depois -- loga direto aqui e já marca essa
        # empresa como a ativa na sessão (mesmo mecanismo do login normal em
        # apps/authentication/views.py:LoginView).
        auth_login(self.request, user, backend="apps.accounts.backends.TenantAwareBackend")
        self.request.session["active_tenant_id"] = str(tenant.id)
        messages.success(self.request, f"Empresa \"{tenant.name}\" criada! Bem-vindo ao Syncora.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:home")
