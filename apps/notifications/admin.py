from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "client", "notification_type", "channel", "status", "tenant")
    list_filter = ("tenant", "notification_type", "channel", "status")
    search_fields = ("client__name",)
    readonly_fields = [f.name for f in NotificationLog._meta.fields]

    def get_queryset(self, request):
        return NotificationLog.all_objects.all()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
