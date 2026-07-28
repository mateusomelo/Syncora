from django import forms

from .models import Anamnesis, Budget, MedicalCertificate, OdontogramTooth, Prescription, Treatment


class AnamnesisForm(forms.ModelForm):
    class Meta:
        model = Anamnesis
        fields = ["allergies", "medications", "medical_conditions", "notes"]
        widgets = {
            "allergies": forms.Textarea(attrs={"rows": 2}),
            "medications": forms.Textarea(attrs={"rows": 2}),
            "medical_conditions": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class ToothConditionForm(forms.ModelForm):
    class Meta:
        model = OdontogramTooth
        fields = ["condition", "notes"]


ToothConditionFormSet = forms.modelformset_factory(OdontogramTooth, form=ToothConditionForm, extra=0)


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = ["tooth_number", "description", "status", "cost"]


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 6})}


class MedicalCertificateForm(forms.ModelForm):
    class Meta:
        model = MedicalCertificate
        fields = ["reason", "days_off"]


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["description", "total", "installment_count", "status"]
