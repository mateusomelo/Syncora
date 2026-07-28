from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsHomeView.as_view(), name="home"),
    path("agendamentos/", views.AppointmentsReportView.as_view(), name="appointments"),
    path("financeiro/", views.FinancialReportView.as_view(), name="financial"),
    path("comissoes/", views.CommissionsReportView.as_view(), name="commissions"),
]
