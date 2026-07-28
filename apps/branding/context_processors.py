from .models import BrandingSettings

PLATFORM_DEFAULTS = {
    "logo": None,
    "logo_dark": None,
    "favicon": None,
    "color_primary": "#111827",
    "color_secondary": "#6b7280",
    "color_button": "#111827",
    "color_link": "#2563eb",
    "color_sidebar": "#111827",
    "color_topbar": "#ffffff",
    "color_card": "#ffffff",
    "color_icons": "#111827",
    "theme_mode": "auto",
    "login_background": None,
    "login_message": "",
    "show_powered_by": True,
}


def branding(request):
    """Disponibiliza `branding` (dict) em todo template — cores/logo/tema da
    empresa resolvida pelo TenantResolutionMiddleware, com fallback para os
    padrões da plataforma quando não há tenant (área do Super Admin) ou a
    empresa ainda não tem BrandingSettings."""

    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return {"branding": PLATFORM_DEFAULTS}

    settings_obj = BrandingSettings.objects.filter(tenant=tenant).first()
    if settings_obj is None:
        return {"branding": PLATFORM_DEFAULTS}

    return {
        "branding": {
            "logo": settings_obj.logo,
            "logo_dark": settings_obj.logo_dark,
            "favicon": settings_obj.favicon,
            "color_primary": settings_obj.color_primary,
            "color_secondary": settings_obj.color_secondary,
            "color_button": settings_obj.color_button,
            "color_link": settings_obj.color_link,
            "color_sidebar": settings_obj.color_sidebar,
            "color_topbar": settings_obj.color_topbar,
            "color_card": settings_obj.color_card,
            "color_icons": settings_obj.color_icons,
            "theme_mode": settings_obj.theme_mode,
            "login_background": settings_obj.login_background,
            "login_message": settings_obj.login_message,
            "show_powered_by": settings_obj.show_powered_by,
        }
    }
