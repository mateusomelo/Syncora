from django.db import models

from apps.core.models import TenantModel


class Professional(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        INACTIVE = "inactive", "Inativo"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="professional_profiles",
        verbose_name="Usuário",
    )
    name = models.CharField(max_length=200, verbose_name="Nome")
    specialties = models.CharField(max_length=255, blank=True, verbose_name="Especialidades")
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="Comissão (%)"
    )
    photo = models.ImageField(upload_to="staff/photos/", blank=True, null=True, verbose_name="Foto")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Status"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkingHours(TenantModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Segunda"
        TUESDAY = 1, "Terça"
        WEDNESDAY = 2, "Quarta"
        THURSDAY = 3, "Quinta"
        FRIDAY = 4, "Sexta"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    professional = models.ForeignKey(
        Professional, on_delete=models.CASCADE, related_name="working_hours", verbose_name="Profissional"
    )
    weekday = models.IntegerField(choices=Weekday.choices, verbose_name="Dia da semana")
    start_time = models.TimeField(verbose_name="Início")
    end_time = models.TimeField(verbose_name="Fim")
    break_start = models.TimeField(null=True, blank=True, verbose_name="Início do intervalo")
    break_end = models.TimeField(null=True, blank=True, verbose_name="Fim do intervalo")

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name_plural = "Working hours"

    def __str__(self):
        return f"{self.professional} · {self.get_weekday_display()}"


class Vacation(TenantModel):
    professional = models.ForeignKey(
        Professional, on_delete=models.CASCADE, related_name="vacations", verbose_name="Profissional"
    )
    start_date = models.DateField(verbose_name="Início")
    end_date = models.DateField(verbose_name="Fim")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Motivo")

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.professional} · {self.start_date} a {self.end_date}"
