from django.db import models

from apps.core.models import TenantModel


class Unit(TenantModel):
    name = models.CharField(max_length=200, verbose_name="Nome")
    address = models.CharField(max_length=255, blank=True, verbose_name="Endereço")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(TenantModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="rooms", verbose_name="Unidade")
    name = models.CharField(max_length=100, verbose_name="Nome")

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
        verbose_name="Profissional",
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, null=True, blank=True, related_name="blocks", verbose_name="Sala"
    )
    type = models.CharField(max_length=30, choices=Type.choices, verbose_name="Tipo")
    title = models.CharField(max_length=200, blank=True, verbose_name="Título")
    start_at = models.DateTimeField(verbose_name="Início")
    end_at = models.DateTimeField(verbose_name="Fim")

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
        "clients.Client", on_delete=models.PROTECT, related_name="appointments", verbose_name="Cliente"
    )
    professional = models.ForeignKey(
        "staff.Professional",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Profissional",
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.PROTECT, related_name="appointments", verbose_name="Serviço"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name="Sala",
    )
    start_at = models.DateTimeField(verbose_name="Início")
    end_at = models.DateTimeField(verbose_name="Fim")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED, verbose_name="Status"
    )
    origin = models.CharField(
        max_length=20, choices=Origin.choices, default=Origin.SYNCORA, verbose_name="Origem"
    )
    cancellation_reason = models.CharField(
        max_length=255, blank=True, verbose_name="Motivo do cancelamento"
    )
    notes = models.TextField(blank=True, verbose_name="Observações")

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
        "clients.Client", on_delete=models.CASCADE, related_name="waitlist_entries", verbose_name="Cliente"
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="waitlist_entries",
        verbose_name="Serviço",
    )
    professional = models.ForeignKey(
        "staff.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waitlist_entries",
        verbose_name="Profissional",
    )
    desired_date = models.DateField(verbose_name="Data desejada")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITING, verbose_name="Status"
    )
    priority = models.PositiveIntegerField(default=0, verbose_name="Prioridade")

    class Meta:
        ordering = ["-priority", "created_at"]

    def __str__(self):
        return f"{self.client} · {self.service} · {self.desired_date}"
