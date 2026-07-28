from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.scheduling.models import Appointment

from .models import Commission, Revenue


@receiver(post_save, sender=Appointment)
def create_revenue_and_commission_on_completion(sender, instance, created, **kwargs):
    """Ao concluir um atendimento, gera automaticamente o lançamento de
    receita (forma de pagamento como Dinheiro por padrão — ajustável depois
    pela recepção) e a comissão do profissional, se ele tiver taxa
    cadastrada. Idempotente: não duplica se o Appointment for salvo de novo
    já concluído."""

    if created or instance.status != Appointment.Status.COMPLETED:
        return

    if not Revenue.objects.filter(appointment=instance).exists():
        Revenue.objects.create(
            tenant=instance.tenant,
            appointment=instance,
            description=f"{instance.service.name} · {instance.client.name}",
            amount=instance.service.price,
            payment_method=Revenue.PaymentMethod.DINHEIRO,
            received_at=timezone.now(),
        )

    commission_rate = instance.professional.commission_rate
    if commission_rate and not Commission.objects.filter(appointment=instance).exists():
        Commission.objects.create(
            tenant=instance.tenant,
            professional=instance.professional,
            appointment=instance,
            amount=instance.service.price * commission_rate / 100,
            percentage=commission_rate,
        )
