from django.db import models

from apps.core.models import TenantModel


class Package(TenantModel):
    name = models.CharField(max_length=200)
    services = models.ManyToManyField("services.Service", related_name="packages")
    session_count = models.PositiveIntegerField(help_text="Quantas sessões o pacote inclui")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TenantModel):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClientPackage(TenantModel):
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="packages_purchased"
    )
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="purchases")
    purchased_at = models.DateTimeField(auto_now_add=True)
    sessions_remaining = models.PositiveIntegerField()

    class Meta:
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.client} · {self.package} ({self.sessions_remaining} restantes)"


class CashRegisterSession(TenantModel):
    class Status(models.TextChoices):
        OPEN = "open", "Aberto"
        CLOSED = "closed", "Fechado"

    opened_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="cash_sessions_opened"
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_amount = models.DecimalField(max_digits=10, decimal_places=2)
    closing_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"Caixa {self.opened_at:%d/%m/%Y} ({self.get_status_display()})"


class CashMovement(TenantModel):
    class Type(models.TextChoices):
        IN = "in", "Entrada"
        OUT = "out", "Saída"

    session = models.ForeignKey(
        CashRegisterSession, on_delete=models.CASCADE, related_name="movements"
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} · R$ {self.amount}"
