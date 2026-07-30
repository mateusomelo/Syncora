from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .middleware import invalidate_tenant_cache
from .models import CustomDomain, Tenant


@receiver(post_save, sender=Tenant)
@receiver(post_delete, sender=Tenant)
def on_tenant_changed(sender, instance, **kwargs):
    invalidate_tenant_cache(instance)


@receiver(post_save, sender=CustomDomain)
@receiver(post_delete, sender=CustomDomain)
def on_custom_domain_changed(sender, instance, **kwargs):
    invalidate_tenant_cache(instance.tenant)
