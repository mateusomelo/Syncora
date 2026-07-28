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
    )
    name = models.CharField(max_length=200)
    specialties = models.CharField(max_length=255, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    photo = models.ImageField(upload_to="staff/photos/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

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
        Professional, on_delete=models.CASCADE, related_name="working_hours"
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name_plural = "Working hours"

    def __str__(self):
        return f"{self.professional} · {self.get_weekday_display()}"


class Vacation(TenantModel):
    professional = models.ForeignKey(
        Professional, on_delete=models.CASCADE, related_name="vacations"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.professional} · {self.start_date} a {self.end_date}"
