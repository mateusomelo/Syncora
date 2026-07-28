from django.contrib import admin

from .models import BrandingSettings


@admin.register(BrandingSettings)
class BrandingSettingsAdmin(admin.ModelAdmin):
    list_display = ("tenant", "theme_mode", "show_powered_by", "updated_at")
    list_filter = ("theme_mode", "show_powered_by")
    search_fields = ("tenant__name",)
