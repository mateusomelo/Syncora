from django import forms

from .models import Professional, WorkingHours


class ProfessionalForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ["name", "specialties", "commission_rate", "photo", "status"]


class WorkingHoursForm(forms.Form):
    """Um form só pra editar os 7 dias da semana de um profissional de uma
    vez (em vez de 7 telas separadas). Não é ModelForm porque não existe
    "o" WorkingHours do profissional -- existem 0 a 7 linhas, uma por dia,
    e cada dia pode estar ligado/desligado independente das outras."""

    def __init__(self, *args, professional, **kwargs):
        self.professional = professional
        super().__init__(*args, **kwargs)
        existing = {wh.weekday: wh for wh in professional.working_hours.all()}
        for value, label in WorkingHours.Weekday.choices:
            wh = existing.get(value)
            self.fields[f"day_{value}_enabled"] = forms.BooleanField(
                required=False, initial=bool(wh), label=label
            )
            self.fields[f"day_{value}_start"] = forms.TimeField(
                required=False, initial=wh.start_time if wh else None, label="Início"
            )
            self.fields[f"day_{value}_end"] = forms.TimeField(
                required=False, initial=wh.end_time if wh else None, label="Fim"
            )
            self.fields[f"day_{value}_break_start"] = forms.TimeField(
                required=False, initial=wh.break_start if wh else None, label="Início do intervalo"
            )
            self.fields[f"day_{value}_break_end"] = forms.TimeField(
                required=False, initial=wh.break_end if wh else None, label="Fim do intervalo"
            )

    def days(self):
        """Agrupa os campos por dia da semana pra facilitar renderizar uma
        linha por dia no template, em vez de iterar `form` cru (que devolve
        os ~35 campos soltos, sem noção de quais 5 pertencem a qual dia)."""
        for value, label in WorkingHours.Weekday.choices:
            yield {
                "label": label,
                "enabled": self[f"day_{value}_enabled"],
                "start": self[f"day_{value}_start"],
                "end": self[f"day_{value}_end"],
                "break_start": self[f"day_{value}_break_start"],
                "break_end": self[f"day_{value}_break_end"],
            }

    def clean(self):
        cleaned = super().clean()
        for value, label in WorkingHours.Weekday.choices:
            if not cleaned.get(f"day_{value}_enabled"):
                continue
            start = cleaned.get(f"day_{value}_start")
            end = cleaned.get(f"day_{value}_end")
            if not start or not end:
                raise forms.ValidationError(f"Informe início e fim de expediente em {label}.")
            if end <= start:
                raise forms.ValidationError(f"O fim tem que ser depois do início em {label}.")
            break_start = cleaned.get(f"day_{value}_break_start")
            break_end = cleaned.get(f"day_{value}_break_end")
            if bool(break_start) != bool(break_end):
                raise forms.ValidationError(
                    f"Informe início e fim do intervalo em {label}, ou deixe os dois em branco."
                )
            if break_start and break_end and break_end <= break_start:
                raise forms.ValidationError(f"O fim do intervalo tem que ser depois do início em {label}.")
        return cleaned

    def save(self):
        for value, _label in WorkingHours.Weekday.choices:
            if self.cleaned_data.get(f"day_{value}_enabled"):
                WorkingHours.objects.update_or_create(
                    professional=self.professional,
                    weekday=value,
                    tenant=self.professional.tenant,
                    defaults={
                        "start_time": self.cleaned_data[f"day_{value}_start"],
                        "end_time": self.cleaned_data[f"day_{value}_end"],
                        "break_start": self.cleaned_data.get(f"day_{value}_break_start"),
                        "break_end": self.cleaned_data.get(f"day_{value}_break_end"),
                    },
                )
            else:
                WorkingHours.objects.filter(professional=self.professional, weekday=value).delete()
