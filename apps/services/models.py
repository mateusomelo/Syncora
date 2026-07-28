from django.db import models

from apps.core.models import TenantModel


class ServiceCategory(TenantModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Service categories"

    def __str__(self):
        return self.name


class Service(TenantModel):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    color = models.CharField(max_length=7, default="#2563eb")
    allowed_professionals = models.ManyToManyField(
        "staff.Professional", blank=True, related_name="services"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
