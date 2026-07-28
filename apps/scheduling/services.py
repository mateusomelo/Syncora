from django.db.models import Q
from django.utils import timezone

from apps.staff.models import Vacation, WorkingHours

from .models import Appointment, Block


def check_conflicts(*, professional, start_at, end_at, room=None, exclude_appointment_id=None):
    """Verifica se um agendamento [start_at, end_at) para `professional`
    (e opcionalmente `room`) é possível. Retorna uma lista de motivos de
    conflito em português, pronta para exibir ao usuário — lista vazia
    significa "sem conflito, pode agendar".

    Ordem de verificação: agenda do profissional, sala, bloqueios pontuais
    (férias/folga/evento/reunião), férias cadastradas, expediente e
    intervalo de almoço.
    """
    reasons = []

    overlapping = Appointment.objects.filter(
        professional=professional, start_at__lt=end_at, end_at__gt=start_at
    ).exclude(status=Appointment.Status.CANCELLED)
    if exclude_appointment_id:
        overlapping = overlapping.exclude(pk=exclude_appointment_id)
    if overlapping.exists():
        reasons.append("Profissional já possui outro atendimento nesse horário.")

    if room is not None:
        overlapping_room = Appointment.objects.filter(
            room=room, start_at__lt=end_at, end_at__gt=start_at
        ).exclude(status=Appointment.Status.CANCELLED)
        if exclude_appointment_id:
            overlapping_room = overlapping_room.exclude(pk=exclude_appointment_id)
        if overlapping_room.exists():
            reasons.append("Sala já está ocupada nesse horário.")

    block_filter = Q(professional=professional)
    if room is not None:
        block_filter |= Q(room=room)
    blocks = Block.objects.filter(start_at__lt=end_at, end_at__gt=start_at).filter(block_filter)
    for block in blocks:
        label = block.get_type_display()
        if block.title:
            label = f"{label} — {block.title}"
        reasons.append(f"Conflito com bloqueio: {label}.")

    # A partir daqui as comparações são de "horário de parede" (expediente,
    # almoço, dia da semana) contra campos Time/Date armazenados em horário
    # local — por isso start_at/end_at precisam ser convertidos para o
    # timezone local antes de extrair .time()/.date()/.weekday(). Sem isso,
    # um datetime vindo do banco (sempre em UTC) dá comparações erradas ainda
    # que o mesmo datetime "recém-limpo" de um form funcionasse por acaso
    # (Django atribui o tzinfo local no cleaning sem converter os dígitos).
    local_start = timezone.localtime(start_at)
    local_end = timezone.localtime(end_at)

    on_vacation = Vacation.objects.filter(
        professional=professional,
        start_date__lte=local_start.date(),
        end_date__gte=local_end.date(),
    ).exists()
    if on_vacation:
        reasons.append("Profissional está de férias nesse período.")

    working_hours = WorkingHours.objects.filter(
        professional=professional, weekday=local_start.weekday()
    ).first()
    if working_hours is None:
        reasons.append("Profissional não tem horário de trabalho cadastrado para esse dia da semana.")
    else:
        start_time, end_time = local_start.time(), local_end.time()
        if start_time < working_hours.start_time or end_time > working_hours.end_time:
            reasons.append("Horário fora do expediente do profissional.")
        if working_hours.break_start and working_hours.break_end:
            if start_time < working_hours.break_end and end_time > working_hours.break_start:
                reasons.append("Horário conflita com o intervalo de almoço do profissional.")

    return reasons
