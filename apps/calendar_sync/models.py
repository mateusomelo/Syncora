from django.db import models

from apps.core.fields import EncryptedTextField
from apps.core.models import TenantModel

# Cores fixas por origem, usadas na Agenda Principal para identificar de
# onde veio cada evento (ver Fase de Agenda / apps/scheduling). Syncora não
# tem "provider" (é a fonte nativa), por isso fica fora deste dict.
SOURCE_COLORS = {
    "google": "#16a34a",
    "outlook": "#1e3a8a",
    "apple": "#6b7280",
}


class CalendarConnection(TenantModel):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google Calendar"
        OUTLOOK = "outlook", "Outlook Calendar"
        APPLE = "apple", "Apple Calendar (iCloud)"

    class SyncDirection(models.TextChoices):
        BIDIRECTIONAL = "bidirectional", "Bidirecional"
        OUT_ONLY = "out_only", "Somente Syncora → Calendário"
        IN_ONLY = "in_only", "Somente Calendário → Syncora"
        DISABLED = "disabled", "Desativada"

    professional = models.ForeignKey(
        "staff.Professional", on_delete=models.CASCADE, related_name="calendar_connections"
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    access_token = EncryptedTextField(blank=True)
    refresh_token = EncryptedTextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    external_calendar_id = models.CharField(max_length=255, blank=True)
    sync_direction = models.CharField(
        max_length=20, choices=SyncDirection.choices, default=SyncDirection.BIDIRECTIONAL
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["professional", "provider"], name="unique_connection_per_provider"
            )
        ]

    def __str__(self):
        return f"{self.professional} · {self.get_provider_display()}"


class ExternalEventMapping(TenantModel):
    connection = models.ForeignKey(
        CalendarConnection, on_delete=models.CASCADE, related_name="event_mappings"
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_mappings",
    )
    external_event_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "external_event_id"],
                name="unique_external_event_per_connection",
            )
        ]
        ordering = ["start_at"]

    @property
    def source_color(self):
        return SOURCE_COLORS.get(self.connection.provider, "#2563eb")

    def __str__(self):
        return f"{self.title} · {self.connection.get_provider_display()}"
