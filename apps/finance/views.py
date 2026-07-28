from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.core.views import TenantRequiredMixin

from .forms import ExpenseForm, RevenueForm
from .models import Commission, Expense, Revenue


class RevenueListView(LoginRequiredMixin, TenantRequiredMixin, ListView):
    template_name = "finance/revenue_list.html"
    context_object_name = "revenues"
    paginate_by = 30

    def get_queryset(self):
        return Revenue.objects.select_related("appointment").all()


class RevenueCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Revenue
    form_class = RevenueForm
    template_name = "finance/revenue_form.html"
    success_url = reverse_lazy("finance:revenue_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class RevenueUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Revenue
    form_class = RevenueForm
    template_name = "finance/revenue_form.html"
    success_url = reverse_lazy("finance:revenue_list")


class ExpenseListView(LoginRequiredMixin, TenantRequiredMixin, ListView):
    template_name = "finance/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 30

    def get_queryset(self):
        return Expense.objects.all()


class ExpenseCreateView(LoginRequiredMixin, TenantRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("finance:expense_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, TenantRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("finance:expense_list")


class ExpenseMarkPaidView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        expense.paid_at = timezone.localdate()
        expense.save(update_fields=["paid_at"])
        return redirect("finance:expense_list")


class CommissionListView(LoginRequiredMixin, TenantRequiredMixin, ListView):
    template_name = "finance/commission_list.html"
    context_object_name = "commissions"
    paginate_by = 30

    def get_queryset(self):
        return Commission.objects.select_related("professional", "appointment__client").all()


class CommissionMarkPaidView(LoginRequiredMixin, TenantRequiredMixin, View):
    def post(self, request, pk):
        commission = get_object_or_404(Commission, pk=pk)
        commission.paid = True
        commission.save(update_fields=["paid"])
        return redirect("finance:commission_list")


class CashFlowView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    template_name = "finance/cash_flow.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_date = date.fromisoformat(self.request.GET.get("start") or today.replace(day=1).isoformat())
        end_date = date.fromisoformat(self.request.GET.get("end") or today.isoformat())

        revenues = Revenue.objects.filter(
            received_at__date__gte=start_date, received_at__date__lte=end_date
        )
        expenses = Expense.objects.filter(due_date__gte=start_date, due_date__lte=end_date)

        total_revenue = revenues.aggregate(total=Sum("amount"))["total"] or 0
        total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0

        ctx.update(
            {
                "start": start_date,
                "end": end_date,
                "revenues": revenues,
                "expenses": expenses,
                "total_revenue": total_revenue,
                "total_expense": total_expense,
                "net": total_revenue - total_expense,
            }
        )
        return ctx
