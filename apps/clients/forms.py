from django import forms

from .models import Client, ClientDocument


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone", "email", "birth_date", "notes", "photo"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ClientDocumentForm(forms.ModelForm):
    class Meta:
        model = ClientDocument
        fields = ["document_type", "file", "description"]
