from django import forms
from django.utils import timezone

from apps.accounts.models import User
from apps.tenants.models import Coupon, Plan, Tenant
from apps.verticals.registry import VERTICALS

SEGMENT_CHOICES = [(key, cfg["label"]) for key, cfg in VERTICALS.items()]


class SignupForm(forms.Form):
    company_name = forms.CharField(max_length=200, label="Nome da empresa")
    segment = forms.ChoiceField(choices=SEGMENT_CHOICES, label="Qual é o seu negócio?")
    subdomain = forms.SlugField(max_length=63, label="Subdomínio")
    admin_email = forms.EmailField(label="Seu e-mail")
    admin_password = forms.CharField(
        widget=forms.PasswordInput, min_length=8, label="Senha"
    )
    plan = forms.ModelChoiceField(queryset=Plan.objects.filter(is_active=True), label="Plano")
    coupon_code = forms.CharField(required=False, label="Cupom de desconto (opcional)")

    def clean_subdomain(self):
        subdomain = self.cleaned_data["subdomain"].lower()
        if Tenant.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError("Esse subdomínio já está em uso.")
        return subdomain

    def clean_admin_email(self):
        email = self.cleaned_data["admin_email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta com esse e-mail.")
        return email

    def clean_coupon_code(self):
        code = self.cleaned_data.get("coupon_code", "").strip()
        if not code:
            return None
        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            raise forms.ValidationError("Cupom inválido.")
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_until):
            raise forms.ValidationError("Esse cupom expirou ou ainda não é válido.")
        if coupon.max_uses is not None and coupon.times_used >= coupon.max_uses:
            raise forms.ValidationError("Esse cupom já atingiu o limite de usos.")
        return coupon
