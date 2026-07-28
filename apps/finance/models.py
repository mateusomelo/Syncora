from django.db import models

from apps.core.models import TenantModel


class Revenue(TenantModel):
    class PaymentMethod(models.TextChoices):
        PIX = "pix", "PIX"
        CARTAO = "cartao", "Cartão"
        DINHEIRO = "dinheiro", "Dinheiro"
        TRANSFERENCIA = "transferencia", "Transferência"

    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenues",
    )
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    received_at = models.DateTimeField()

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"R$ {self.amount} · {self.get_payment_method_display()} · {self.received_at:%d/%m/%Y}"


class Expense(TenantModel):
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.category} · R$ {self.amount} · vence {self.due_date:%d/%m/%Y}"

    @property
    def is_paid(self):
        return self.paid_at is not None


class Commission(TenantModel):
    professional = models.ForeignKey(
        "staff.Professional", on_delete=models.CASCADE, related_name="commissions"
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.CASCADE, related_name="commissions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["appointment"], name="unique_commission_per_appointment"
            )
        ]

    def __str__(self):
        return f"{self.professional} · R$ {self.amount} ({self.percentage}%)"
