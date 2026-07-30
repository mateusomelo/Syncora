from django import forms

from .models import BrandingSettings

COLOR_FIELDS = [
    "color_primary",
    "color_secondary",
    "color_button",
    "color_link",
    "color_sidebar",
    "color_topbar",
    "color_card",
    "color_icons",
]


class BrandingSettingsForm(forms.ModelForm):
    class Meta:
        model = BrandingSettings
        fields = [
            "logo",
            "logo_dark",
            "favicon",
            *COLOR_FIELDS,
            "theme_mode",
            "login_background",
            "login_message",
            "show_powered_by",
        ]
        widgets = {field: forms.TextInput(attrs={"type": "color"}) for field in COLOR_FIELDS}
        labels = {
            "logo": "Logo (fundo claro)",
            "logo_dark": "Logo (fundo escuro)",
            "favicon": "Favicon",
            "color_primary": "Primária",
            "color_secondary": "Secundária",
            "color_button": "Botões",
            "color_link": "Links",
            "color_sidebar": "Menu lateral",
            "color_topbar": "Topo",
            "color_card": "Cartões",
            "color_icons": "Ícones",
            "theme_mode": "Tema",
            "login_background": "Imagem de fundo",
            "login_message": "Mensagem de boas-vindas",
            "show_powered_by": 'Mostrar "powered by Syncora" no rodapé',
        }
