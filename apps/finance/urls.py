from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("caixa/", views.CashFlowView.as_view(), name="cash_flow"),
    path("receitas/", views.RevenueListView.as_view(), name="revenue_list"),
    path("receitas/novo/", views.RevenueCreateView.as_view(), name="revenue_create"),
    path("receitas/<int:pk>/editar/", views.RevenueUpdateView.as_view(), name="revenue_update"),
    path("despesas/", views.ExpenseListView.as_view(), name="expense_list"),
    path("despesas/novo/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("despesas/<int:pk>/editar/", views.ExpenseUpdateView.as_view(), name="expense_update"),
    path("despesas/<int:pk>/pagar/", views.ExpenseMarkPaidView.as_view(), name="expense_mark_paid"),
    path("comissoes/", views.CommissionListView.as_view(), name="commission_list"),
    path(
        "comissoes/<int:pk>/pagar/",
        views.CommissionMarkPaidView.as_view(),
        name="commission_mark_paid",
    ),
]
