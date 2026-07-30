from django import forms

from apps.accounts.forms import generate_password
from apps.accounts.models import User
from apps.tenants.models import Tenant


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
