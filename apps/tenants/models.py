import uuid

from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Plan(TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    max_users = models.PositiveIntegerField()
    max_professionals = models.PositiveIntegerField()
    max_appointments_per_month = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.name


class Tenant(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Ativo"
        SUSPENDED = "suspended", "Suspenso"
        CANCELLED = "cancelled", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    subdomain = models.SlugField(max_length=63, unique=True)
    cnpj = models.CharField(max_length=18, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TRIAL
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="tenants")
    suspended_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_operational(self):
        return self.status in {self.Status.TRIAL, self.Status.ACTIVE}


class CustomDomain(TimeStampedModel):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="custom_domains"
    )
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    ssl_status = models.CharField(max_length=20, default="pending")

    def __str__(self):
        return self.domain


class FeatureFlag(TimeStampedModel):
    class Key(models.TextChoices):
        FINANCEIRO = "financeiro", "Financeiro"
        RELATORIOS = "relatorios", "Relatórios"
        WHATSAPP = "whatsapp", "WhatsApp"
        ESTOQUE = "estoque", "Estoque"
        PRONTUARIO = "prontuario", "Prontuário"
        ODONTOGRAMA = "odontograma", "Odontograma"
        PSICOLOGIA = "psicologia", "Psicologia"
        BARBEARIA = "barbearia", "Barbearia"
        API = "api", "API"
        INTEGRACOES = "integracoes", "Integrações"
        DASHBOARD_AVANCADO = "dashboard_avancado", "Dashboard Avançado"
        MULTIUNIDADES = "multiunidades", "Multiunidades"
        ASSINATURAS_ONLINE = "assinaturas_online", "Assinaturas Online"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="feature_flags"
    )
    key = models.CharField(max_length=30, choices=Key.choices)
    enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "key"], name="unique_tenant_feature_flag"
            )
        ]

    def __str__(self):
        return f"{self.tenant} · {self.key} = {self.enabled}"


class TenantSubscription(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        PAST_DUE = "past_due", "Em atraso"
        CANCELLED = "cancelled", "Cancelada"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    period_start = models.DateField()
    period_end = models.DateField()
    gateway_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-period_start"]


class Coupon(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentual"
        FIXED = "fixed", "Valor fixo"

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
