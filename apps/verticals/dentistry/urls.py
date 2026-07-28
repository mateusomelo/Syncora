from django.urls import path

from . import views

app_name = "dentistry"

urlpatterns = [
    path("pacientes/", views.PatientListView.as_view(), name="patient_list"),
    path("orcamentos/", views.BudgetListView.as_view(), name="budget_list"),
    path(
        "pacientes/<int:client_pk>/prontuario/",
        views.ClientDentalRecordView.as_view(),
        name="dental_record",
    ),
    path(
        "pacientes/<int:client_pk>/odontograma/criar/",
        views.OdontogramCreateView.as_view(),
        name="odontogram_create",
    ),
    path(
        "pacientes/<int:client_pk>/odontograma/atualizar/",
        views.OdontogramUpdateView.as_view(),
        name="odontogram_update",
    ),
    path(
        "pacientes/<int:client_pk>/anamnese/",
        views.AnamnesisEditView.as_view(),
        name="anamnesis_edit",
    ),
    path(
        "pacientes/<int:client_pk>/tratamentos/novo/",
        views.TreatmentCreateView.as_view(),
        name="treatment_create",
    ),
    path(
        "pacientes/<int:client_pk>/receitas/novo/",
        views.PrescriptionCreateView.as_view(),
        name="prescription_create",
    ),
    path(
        "pacientes/<int:client_pk>/atestados/novo/",
        views.MedicalCertificateCreateView.as_view(),
        name="certificate_create",
    ),
    path(
        "pacientes/<int:client_pk>/orcamentos/novo/",
        views.BudgetCreateView.as_view(),
        name="budget_create",
    ),
    path(
        "pacientes/<int:client_pk>/parcelas/<int:pk>/pagar/",
        views.InstallmentMarkPaidView.as_view(),
        name="installment_mark_paid",
    ),
]
