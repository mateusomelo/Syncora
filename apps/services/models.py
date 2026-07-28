from django.db import models

from apps.core.models import TenantModel


class ServiceCategory(TenantModel):
    name = models.CharField(max_length=100, verbose_name="Nome")

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
        verbose_name="Categoria",
    )
    name = models.CharField(max_length=200, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    duration_minutes = models.PositiveIntegerField(verbose_name="Duração (minutos)")
    color = models.CharField(max_length=7, default="#2563eb", verbose_name="Cor")
    allowed_professionals = models.ManyToManyField(
        "staff.Professional", blank=True, related_name="services", verbose_name="Profissionais habilitados"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
