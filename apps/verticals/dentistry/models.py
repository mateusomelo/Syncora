from django.db import models

from apps.core.models import TenantModel

# Notação FDI (padrão internacional/brasileiro): quadrantes 1-4, dentes 1-8
# em cada um — 32 dentes permanentes ao todo.
FDI_TEETH = [
    q * 10 + n for q in (1, 2, 3, 4) for n in range(1, 9)
]


class Odontogram(TenantModel):
    client = models.OneToOneField(
        "clients.Client", on_delete=models.CASCADE, related_name="odontogram"
    )

    def __str__(self):
        return f"Odontograma · {self.client}"

    @classmethod
    def create_for_client(cls, client):
        odontogram = cls.objects.create(tenant=client.tenant, client=client)
        OdontogramTooth.objects.bulk_create(
            [
                OdontogramTooth(tenant=client.tenant, odontogram=odontogram, tooth_number=n)
                for n in FDI_TEETH
            ]
        )
        return odontogram


class OdontogramTooth(TenantModel):
    class Condition(models.TextChoices):
        HEALTHY = "healthy", "Hígido"
        CARIES = "caries", "Cariado"
        RESTORED = "restored", "Restaurado"
        MISSING = "missing", "Ausente"
        IMPLANT = "implant", "Implante"
        CROWN = "crown", "Coroa"
        CANAL = "canal", "Tratamento de canal"

    odontogram = models.ForeignKey(Odontogram, on_delete=models.CASCADE, related_name="teeth")
    tooth_number = models.PositiveSmallIntegerField()
    condition = models.CharField(
        max_length=20, choices=Condition.choices, default=Condition.HEALTHY
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["odontogram", "tooth_number"], name="unique_tooth_per_odontogram"
            )
        ]
        ordering = ["tooth_number"]

    def __str__(self):
        return f"Dente {self.tooth_number} · {self.get_condition_display()}"


class Anamnesis(TenantModel):
    client = models.OneToOneField(
        "clients.Client", on_delete=models.CASCADE, related_name="anamnesis"
    )
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Anamnese · {self.client}"


class Treatment(TenantModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planejado"
        IN_PROGRESS = "in_progress", "Em andamento"
        COMPLETED = "completed", "Concluído"

    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="treatments")
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dental_treatments",
    )
    tooth_number = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.description} · {self.client}"


class Prescription(TenantModel):
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="prescriptions"
    )
    content = models.TextField()
    issued_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Receita · {self.client} · {self.issued_at}"


class MedicalCertificate(TenantModel):
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="medical_certificates"
    )
    reason = models.CharField(max_length=255)
    days_off = models.PositiveIntegerField(default=0)
    issued_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Atestado · {self.client} · {self.issued_at}"


class Budget(TenantModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"

    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="budgets")
    description = models.CharField(max_length=255)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    installment_count = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Orçamento · {self.client} · R$ {self.total}"


class Installment(TenantModel):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="installments")
    number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "number"], name="unique_installment_number_per_budget"
            )
        ]

    def __str__(self):
        return f"Parcela {self.number} · {self.budget}"

    @property
    def is_paid(self):
        return self.paid_at is not None
