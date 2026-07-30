from apps.verticals.registry import DEFAULT_THEME, get_active_theme

from .models import BrandingSettings

PLATFORM_DEFAULTS = {
    "logo": None,
    "logo_dark": None,
    "favicon": None,
    "theme_mode": "auto",
    "login_background": None,
    "login_message": "",
    "show_powered_by": True,
    **DEFAULT_THEME,
}


def branding(request):
    """Disponibiliza `branding` (dict) em todo template — logo/tema da
    empresa resolvida pelo TenantResolutionMiddleware, com fallback para os
    padrões da plataforma quando não há tenant (área do Super Admin) ou a
    empresa ainda não tem BrandingSettings.

    As cores NÃO são mais escolha da empresa -- vêm fixas do módulo vertical
    ativo (get_active_theme), pra cada segmento (barbearia/odontologia/
    psicologia) ter uma identidade visual própria e consistente entre
    empresas do mesmo tipo. Só logo/favicon/tema claro-escuro/tela de login
    continuam editáveis em BrandingSettings."""

    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return {"branding": PLATFORM_DEFAULTS}

    settings_obj = BrandingSettings.objects.filter(tenant=tenant).first()
    theme = get_active_theme(tenant)

    if settings_obj is None:
        return {"branding": {**PLATFORM_DEFAULTS, **theme}}

    return {
        "branding": {
            "logo": settings_obj.logo,
            "logo_dark": settings_obj.logo_dark,
            "favicon": settings_obj.favicon,
            "theme_mode": settings_obj.theme_mode,
            "login_background": settings_obj.login_background,
            "login_message": settings_obj.login_message,
            "show_powered_by": settings_obj.show_powered_by,
            **theme,
        }
    }
