from django import forms

from apps.staff.models import Professional

from .models import Service, ServiceCategory


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "category",
            "name",
            "description",
            "price",
            "duration_minutes",
            "color",
            "allowed_professionals",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "allowed_professionals": forms.CheckboxSelectMultiple(),
            "color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ModelForm monta o queryset de campos FK/M2M uma única vez, na
        # importação do módulo (definição da classe) — e nesse momento não
        # existe request/tenant ativo, então TenantManager devolve .none().
        # Reatribuir aqui, em __init__, garante que o queryset é reavaliado
        # a cada instanciação do form (dentro de uma request de verdade),
        # já filtrado corretamente pelo tenant corrente.
        self.fields["category"].queryset = ServiceCategory.objects.all()
        self.fields["allowed_professionals"].queryset = Professional.objects.all()
