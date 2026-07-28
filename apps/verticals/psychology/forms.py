from django import forms

from apps.clients.models import Client
from apps.staff.models import Professional

from .models import ClinicalRecord, SessionNote


class ClinicalRecordForm(forms.ModelForm):
    class Meta:
        model = ClinicalRecord
        fields = ["client", "responsible_professional"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ver apps/core/models.py (TenantManager) — queryset precisa ser
        # reatribuído aqui, não herdado do Meta.fields.
        self.fields["client"].queryset = Client.objects.all()
        self.fields["responsible_professional"].queryset = Professional.objects.filter(
            status=Professional.Status.ACTIVE
        )


class SessionNoteForm(forms.ModelForm):
    class Meta:
        model = SessionNote
        fields = ["evolution_text", "is_confidential"]
        widgets = {"evolution_text": forms.Textarea(attrs={"rows": 5})}
