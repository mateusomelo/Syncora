from django.db import models

from apps.core.models import TenantModel


class Unit(TenantModel):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(TenantModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["unit", "name"]

    def __str__(self):
        return f"{self.unit} · {self.name}"


class Block(TenantModel):
    """Exceção pontual (férias, folga, evento, reunião, data comemorativa).

    Padrões recorrentes (ex.: almoço diário) já são cobertos por
    apps.staff.WorkingHours.break_start/break_end — Block é só para
    exceções pontuais, por isso não tem recurrence_rule."""

    class Type(models.TextChoices):
        ALMOCO = "almoco", "Almoço"
        FERIAS = "ferias", "Férias"
        FOLGA = "folga", "Folga"
        EVENTO = "evento", "Evento interno"
        REUNIAO = "reuniao", "Reunião"
        DATA_COMEMORATIVA = "data_comemorativa", "Data comemorativa"

    professional = models.ForeignKey(
        "staff.Professional",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blocks",
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, null=True, blank=True, related_name="blocks"
    )
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    class Meta:
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.get_type_display()} · {self.title or self.professional or self.room}"


class Appointment(TenantModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Agendado"
        CONFIRMED = "confirmed", "Confirmado"
        CHECKED_IN = "checked_in", "Check-in"
        COMPLETED = "completed", "Concluído"
        CANCELLED = "cancelled", "Cancelado"
        NO_SHOW = "no_show", "Não compareceu"

    class Origin(models.TextChoices):
        SYNCORA = "syncora", "Syncora"
        GOOGLE = "google", "Google Calendar"
        OUTLOOK = "outlook", "Outlook"
        APPLE = "apple", "Apple Calendar"

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="appointments"
    )
    professional = models.ForeignKey(
        "staff.Professional", on_delete=models.PROTECT, related_name="appointments"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.PROTECT, related_name="appointments"
    )
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments"
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    origin = models.CharField(max_length=20, choices=Origin.choices, default=Origin.SYNCORA)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["tenant", "professional", "start_at"]),
            models.Index(fields=["tenant", "room", "start_at"]),
        ]

    def __str__(self):
        return f"{self.client} · {self.service} · {self.start_at:%d/%m %H:%M}"


class WaitList(TenantModel):
    class Status(models.TextChoices):
        WAITING = "waiting", "Aguardando"
        FULFILLED = "fulfilled", "Atendido"
        CANCELLED = "cancelled", "Cancelado"

    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    professional = models.ForeignKey(
        "staff.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waitlist_entries",
    )
    desired_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-priority", "created_at"]

    def __str__(self):
        return f"{self.client} · {self.service} · {self.desired_date}"
