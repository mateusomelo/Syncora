from django.contrib import admin

from .models import ClinicalRecord, SessionNote


@admin.register(ClinicalRecord)
class ClinicalRecordAdmin(admin.ModelAdmin):
    list_display = ("client", "responsible_professional", "tenant")
    list_filter = ("tenant",)
    filter_horizontal = ("authorized_users",)

    def get_queryset(self, request):
        return ClinicalRecord.all_objects.all()


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ("clinical_record", "created_by", "created_at", "is_confidential", "tenant")
    list_filter = ("tenant", "is_confidential")

    def get_queryset(self, request):
        return SessionNote.all_objects.all()
