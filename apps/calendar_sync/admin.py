from django.contrib import admin

from .models import CalendarConnection, ExternalEventMapping


@admin.register(CalendarConnection)
class CalendarConnectionAdmin(admin.ModelAdmin):
    list_display = ("professional", "provider", "sync_direction", "is_active", "last_synced_at", "tenant")
    list_filter = ("tenant", "provider", "sync_direction", "is_active")
    readonly_fields = ("access_token", "refresh_token")

    def get_queryset(self, request):
        return CalendarConnection.all_objects.all()


@admin.register(ExternalEventMapping)
class ExternalEventMappingAdmin(admin.ModelAdmin):
    list_display = ("title", "connection", "start_at", "end_at", "tenant")
    list_filter = ("tenant", "connection__provider")

    def get_queryset(self, request):
        return ExternalEventMapping.all_objects.all()
