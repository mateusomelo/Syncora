import secrets
import string

from django import forms

from .models import Membership, User


def generate_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


class MembershipInviteForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail")
    role = forms.ChoiceField(label="Papel", choices=Membership.Role.choices)
    password = forms.CharField(
        label="Senha inicial",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Deixe em branco para gerar uma senha automática.",
    )

    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user = User.objects.filter(email=email).first()
        if user and Membership.objects.filter(tenant=self.tenant, user=user).exists():
            raise forms.ValidationError("Esse e-mail já tem acesso a essa empresa.")
        return email

    def save(self):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"] or generate_password()
        user = User.objects.filter(email=email).first()
        generated = False
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
            )
            generated = True
        membership = Membership.objects.create(
            user=user, tenant=self.tenant, role=self.cleaned_data["role"]
        )
        return membership, (password if generated else None)


class MembershipRoleForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["role", "is_active"]
