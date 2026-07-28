from datetime import timedelta

from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError

from .models import Appointment
from .services import check_conflicts


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "client",
            "professional",
            "service",
            "room",
            "start_at",
            "end_at",
            "status",
            "origin",
            "cancellation_reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "end_at", "status", "origin", "created_at", "updated_at"]

    def validate(self, attrs):
        professional = attrs.get("professional") or getattr(self.instance, "professional", None)
        service = attrs.get("service") or getattr(self.instance, "service", None)
        start_at = attrs.get("start_at") or getattr(self.instance, "start_at", None)
        room = attrs.get("room") if "room" in attrs else getattr(self.instance, "room", None)

        if professional and service and start_at:
            end_at = start_at + timedelta(minutes=service.duration_minutes)
            conflicts = check_conflicts(
                professional=professional,
                start_at=start_at,
                end_at=end_at,
                room=room,
                exclude_appointment_id=self.instance.pk if self.instance else None,
            )
            if conflicts:
                raise ValidationError({"non_field_errors": conflicts})
            attrs["end_at"] = end_at
        return attrs


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related("client", "professional", "service", "room").all()
        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(start_at__date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
