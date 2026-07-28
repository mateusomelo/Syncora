from datetime import date
from decimal import Decimal

from .models import Installment


def generate_installments(budget):
    """Divide budget.total em budget.installment_count parcelas mensais
    (a diferença de arredondamento vai toda para a última parcela)."""

    count = budget.installment_count
    base_amount = (budget.total / count).quantize(Decimal("0.01"))
    remainder = budget.total - (base_amount * count)

    today = date.today()
    installments = []
    for i in range(1, count + 1):
        amount = base_amount + remainder if i == count else base_amount
        month_index = today.month - 1 + (i - 1)
        year = today.year + month_index // 12
        month = month_index % 12 + 1
        day = min(today.day, 28)
        installments.append(
            Installment(
                tenant=budget.tenant,
                budget=budget,
                number=i,
                amount=amount,
                due_date=date(year, month, day),
            )
        )
    return Installment.objects.bulk_create(installments)
