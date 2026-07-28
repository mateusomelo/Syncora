from django.contrib import admin

from .models import Appointment, Block, Room, Unit, WaitList


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "address")
    list_filter = ("tenant",)

    def get_queryset(self, request):
        return Unit.all_objects.all()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "tenant")
    list_filter = ("tenant", "unit")

    def get_queryset(self, request):
        return Room.all_objects.all()


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("type", "professional", "room", "start_at", "end_at", "tenant")
    list_filter = ("tenant", "type")

    def get_queryset(self, request):
        return Block.all_objects.all()


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "start_at",
        "client",
        "professional",
        "service",
        "status",
        "origin",
        "tenant",
    )
    list_filter = ("tenant", "status", "origin")
    search_fields = ("client__name", "professional__name")

    def get_queryset(self, request):
        return Appointment.all_objects.all()


@admin.register(WaitList)
class WaitListAdmin(admin.ModelAdmin):
    list_display = ("client", "service", "professional", "desired_date", "status", "priority")
    list_filter = ("tenant", "status")

    def get_queryset(self, request):
        return WaitList.all_objects.all()
