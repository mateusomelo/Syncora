from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from apps.accounts.models import Membership, User
from apps.branding.models import BrandingSettings
from apps.tenants.models import Tenant

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

        self._subdomain = tenant.subdomain
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("onboarding:signup_success") + f"?subdomain={self._subdomain}"


class SignupSuccessView(TemplateView):
    template_name = "onboarding/signup_success.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subdomain"] = self.request.GET.get("subdomain", "")
        ctx["tenant_base_domain"] = settings.TENANT_BASE_DOMAIN
        return ctx
