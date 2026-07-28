from django.db import models

from apps.core.models import TimeStampedModel


class BrandingSettings(TimeStampedModel):
    class ThemeMode(models.TextChoices):
        LIGHT = "light", "Claro"
        DARK = "dark", "Escuro"
        AUTO = "auto", "Automático (segue o sistema)"

    tenant = models.OneToOneField(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="branding"
    )

    logo = models.ImageField(upload_to="branding/logos/", blank=True, null=True)
    logo_dark = models.ImageField(upload_to="branding/logos/", blank=True, null=True)
    favicon = models.ImageField(upload_to="branding/favicons/", blank=True, null=True)

    color_primary = models.CharField(max_length=7, default="#111827")
    color_secondary = models.CharField(max_length=7, default="#6b7280")
    color_button = models.CharField(max_length=7, default="#111827")
    color_link = models.CharField(max_length=7, default="#2563eb")
    color_sidebar = models.CharField(max_length=7, default="#111827")
    color_topbar = models.CharField(max_length=7, default="#ffffff")
    color_card = models.CharField(max_length=7, default="#ffffff")
    color_icons = models.CharField(max_length=7, default="#111827")
    chart_colors = models.JSONField(default=list, blank=True)

    theme_mode = models.CharField(
        max_length=10, choices=ThemeMode.choices, default=ThemeMode.AUTO
    )

    login_background = models.ImageField(upload_to="branding/login/", blank=True, null=True)
    login_message = models.CharField(max_length=255, blank=True)

    show_powered_by = models.BooleanField(default=True)

    def __str__(self):
        return f"Branding · {self.tenant}"
