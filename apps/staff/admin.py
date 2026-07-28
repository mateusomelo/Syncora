from django.contrib import admin

from .models import Professional, Vacation, WorkingHours


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 0


class VacationInline(admin.TabularInline):
    model = Vacation
    extra = 0


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "status", "commission_rate")
    list_filter = ("tenant", "status")
    search_fields = ("name", "specialties")
    inlines = [WorkingHoursInline, VacationInline]

    def get_queryset(self, request):
        return Professional.all_objects.all()
