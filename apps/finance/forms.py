from django import forms

from .models import Expense, Revenue


class RevenueForm(forms.ModelForm):
    class Meta:
        model = Revenue
        fields = ["description", "amount", "payment_method", "received_at"]
        widgets = {
            "received_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "description", "amount", "due_date", "paid_at"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "paid_at": forms.DateInput(attrs={"type": "date"}),
        }
