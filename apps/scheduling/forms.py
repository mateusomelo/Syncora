from datetime import timedelta

from django import forms

from apps.clients.models import Client
from apps.services.models import Service
from apps.staff.models import Professional

from .models import Appointment, Room
from .services import check_conflicts


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["client", "professional", "service", "room", "start_at", "notes"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ver apps/core/models.py (TenantManager) — queryset precisa ser
        # reatribuído aqui em __init__, não herdado do Meta.fields.
        self.fields["client"].queryset = Client.objects.all()
        self.fields["professional"].queryset = Professional.objects.filter(
            status=Professional.Status.ACTIVE
        )
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        self.fields["room"].queryset = Room.objects.all()
        self.fields["room"].required = False

    def clean(self):
        cleaned_data = super().clean()
        professional = cleaned_data.get("professional")
        service = cleaned_data.get("service")
        start_at = cleaned_data.get("start_at")
        room = cleaned_data.get("room")

        if professional and service and start_at:
            end_at = start_at + timedelta(minutes=service.duration_minutes)
            cleaned_data["end_at"] = end_at
            conflicts = check_conflicts(
                professional=professional,
                start_at=start_at,
                end_at=end_at,
                room=room,
                exclude_appointment_id=self.instance.pk,
            )
            if conflicts:
                raise forms.ValidationError(conflicts)
        return cleaned_data

    def save(self, commit=True):
        self.instance.end_at = self.cleaned_data["end_at"]
        return super().save(commit=commit)


class CancelAppointmentForm(forms.Form):
    reason = forms.CharField(
        label="Motivo do cancelamento", widget=forms.Textarea(attrs={"rows": 2})
    )
