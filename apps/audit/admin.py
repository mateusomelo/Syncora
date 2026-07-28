from django.contrib import admin

from .models import AuditLog, ImpersonationSession


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "tenant", "action", "target_model", "target_id", "is_impersonated")
    list_filter = ("action", "target_model", "is_impersonated", "tenant")
    search_fields = ("target_id", "actor__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ImpersonationSession)
class ImpersonationSessionAdmin(admin.ModelAdmin):
    list_display = ("super_admin", "tenant", "started_at", "ended_at", "reason")
    list_filter = ("tenant",)
