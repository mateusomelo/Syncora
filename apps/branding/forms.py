from django import forms

from .models import BrandingSettings


class BrandingSettingsForm(forms.ModelForm):
    """Cor não é campo editável aqui de propósito -- vem fixa do módulo
    vertical ativo (apps/verticals/registry.get_active_theme). Só logo,
    favicon, tema claro/escuro e tela de login são escolha da empresa."""

    class Meta:
        model = BrandingSettings
        fields = [
            "logo",
            "logo_dark",
            "favicon",
            "theme_mode",
            "login_background",
            "login_message",
            "show_powered_by",
        ]
        labels = {
            "logo": "Logo (fundo claro)",
            "logo_dark": "Logo (fundo escuro)",
            "favicon": "Favicon",
            "theme_mode": "Tema",
            "login_background": "Imagem de fundo",
            "login_message": "Mensagem de boas-vindas",
            "show_powered_by": 'Mostrar "powered by Syncora" no rodapé',
        }
