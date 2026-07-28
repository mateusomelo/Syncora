from django.db import models
from django.utils import timezone

from apps.core.context import get_current_tenant_id


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted_at = timezone.now()
        return self.save(using=using, update_fields=["deleted_at"])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class TenantQuerySet(SoftDeleteQuerySet):
    pass


class TenantManager(models.Manager):
    """Escopa toda query automaticamente pelo tenant corrente.

    Quando não há tenant no contexto (nenhuma request em andamento — ex.:
    um shell solto), devolve queryset vazio de propósito: nunca vazar dado
    "por acidente" fora de uma requisição resolvida por tenant. Use
    `all_objects` deliberadamente para acesso cross-tenant (Super Admin).

    Cuidado ao referenciar um TenantModel via FK/M2M em ModelForm ou DRF
    ModelSerializer: o Django monta o queryset desses campos uma única vez,
    na definição da classe (import do módulo) — momento em que não existe
    tenant algum no contextvar, então o campo fica com um queryset vazio
    "congelado" para sempre. Sempre reatribua `self.fields["campo"].queryset`
    dentro de `__init__` (form) ou `get_fields()`/`__init__` (serializer),
    para que seja reavaliado a cada instanciação, já dentro de uma request
    real. Ver apps/services/forms.py:ServiceForm para o padrão.
    """

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db).alive()
        tenant_id = get_current_tenant_id()
        if tenant_id is None:
            return qs.none()
        return qs.filter(tenant_id=tenant_id)


class TenantAllObjectsManager(models.Manager):
    """Sem filtro de tenant nem de soft-delete. Reservado para o Super Admin
    e para jobs internos de plataforma (nunca exposto a views de tenant)."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)


class TenantModel(TimeStampedModel, SoftDeleteModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="+"
    )

    objects = TenantManager()
    all_objects = TenantAllObjectsManager()

    class Meta:
        abstract = True
