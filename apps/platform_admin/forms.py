from django import forms

from apps.accounts.forms import generate_password
from apps.accounts.models import User
from apps.tenants.models import Tenant
from apps.verticals.registry import VERTICALS

SEGMENT_CHOICES = [(key, cfg["label"]) for key, cfg in VERTICALS.items()]


class PlatformAdminInviteForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail")
    password = forms.CharField(
        label="Senha inicial",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Deixe em branco para gerar uma senha automática.",
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta com esse e-mail.")
        return email

    def save(self):
        password = self.cleaned_data["password"] or generate_password()
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=password,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            is_platform_admin=True,
        )
        return user, password


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "trade_name", "subdomain", "cnpj", "plan"]
        labels = {
            "name": "Razão social",
            "trade_name": "Nome fantasia",
            "subdomain": "Subdomínio",
            "cnpj": "CNPJ",
            "plan": "Plano",
        }


class TenantCreateForm(TenantForm):
    """Só na criação (TenantCreateView) -- monta a empresa já pronta pra uso:
    liga o módulo do segmento escolhido e cria o primeiro acesso (admin
    master) no mesmo passo, em vez de exigir 2 telas separadas depois.
    TenantUpdateView continua no TenantForm puro -- editar uma empresa que já
    existe não deve pedir e-mail/senha de novo."""

    segment = forms.ChoiceField(
        choices=SEGMENT_CHOICES,
        label="Segmento",
        help_text="Liga automaticamente o módulo certo pra essa empresa.",
    )
    admin_email = forms.EmailField(label="E-mail do administrador")
    admin_password = forms.CharField(
        label="Senha inicial",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Deixe em branco para gerar uma senha automática.",
    )

    field_order = ["name", "trade_name", "subdomain", "cnpj", "plan", "segment", "admin_email", "admin_password"]

    def clean_admin_email(self):
        email = self.cleaned_data["admin_email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta com esse e-mail.")
        return email
