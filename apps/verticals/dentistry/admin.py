from django.contrib import admin

from .models import (
    Anamnesis,
    Budget,
    Installment,
    MedicalCertificate,
    Odontogram,
    OdontogramTooth,
    Prescription,
    Treatment,
)


class OdontogramToothInline(admin.TabularInline):
    model = OdontogramTooth
    extra = 0


@admin.register(Odontogram)
class OdontogramAdmin(admin.ModelAdmin):
    list_display = ("client", "tenant", "updated_at")
    list_filter = ("tenant",)
    inlines = [OdontogramToothInline]

    def get_queryset(self, request):
        return Odontogram.all_objects.all()


@admin.register(Anamnesis)
class AnamnesisAdmin(admin.ModelAdmin):
    list_display = ("client", "tenant")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return Anamnesis.all_objects.all()


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ("client", "description", "status", "cost", "tenant")
    list_filter = ("tenant", "status")

    def get_queryset(self, request):
        return Treatment.all_objects.all()


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("client", "issued_at", "tenant")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return Prescription.all_objects.all()


@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    list_display = ("client", "reason", "days_off", "issued_at", "tenant")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return MedicalCertificate.all_objects.all()


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("client", "description", "total", "status", "tenant")
    list_filter = ("tenant", "status")
    inlines = [InstallmentInline]

    def get_queryset(self, request):
        return Budget.all_objects.all()
