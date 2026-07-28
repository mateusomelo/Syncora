from django import forms

from .models import Professional


class ProfessionalForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ["name", "specialties", "commission_rate", "photo", "status"]
