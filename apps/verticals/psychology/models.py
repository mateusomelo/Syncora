from django.db import models

from apps.core.models import TenantModel


class ClinicalRecord(TenantModel):
    """Prontuário psicológico. Acesso deliberadamente mais restrito que os
    outros verticais (LGPD, dado de saúde mental é categoria sensível):
    só o profissional responsável ou quem recebeu concessão explícita
    enxerga o conteúdo — nem admin_empresa nem Super Admin por padrão. Ver
    user_has_access() e apps/verticals/psychology/views.py."""

    client = models.OneToOneField(
        "clients.Client", on_delete=models.CASCADE, related_name="clinical_record"
    )
    responsible_professional = models.ForeignKey(
        "staff.Professional", on_delete=models.PROTECT, related_name="clinical_records"
    )
    authorized_users = models.ManyToManyField(
        "accounts.User", blank=True, related_name="authorized_clinical_records"
    )

    def __str__(self):
        return f"Prontuário · {self.client}"

    def user_has_access(self, user):
        if not user.is_authenticated:
            return False
        # Nem o Super Admin (cross-tenant, is_platform_admin) vê por padrão
        # — só com concessão explícita, igual a qualquer outro usuário.
        if self.responsible_professional.user_id == user.id:
            return True
        return self.authorized_users.filter(pk=user.id).exists()


class SessionNote(TenantModel):
    clinical_record = models.ForeignKey(
        ClinicalRecord, on_delete=models.CASCADE, related_name="session_notes"
    )
    appointment = models.OneToOneField(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_note",
    )
    evolution_text = models.TextField()
    is_confidential = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="session_notes_authored"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Evolução · {self.clinical_record.client} · {self.created_at:%d/%m/%Y}"
