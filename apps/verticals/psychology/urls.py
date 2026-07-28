from django.urls import path

from . import views

app_name = "psychology"

urlpatterns = [
    path("prontuarios/", views.ClinicalRecordListView.as_view(), name="clinical_record_list"),
    path(
        "prontuarios/novo/", views.ClinicalRecordCreateView.as_view(), name="clinical_record_create"
    ),
    path(
        "prontuarios/<int:record_pk>/",
        views.ClinicalRecordDetailView.as_view(),
        name="clinical_record_detail",
    ),
    path(
        "prontuarios/<int:record_pk>/evolucoes/nova/",
        views.SessionNoteCreateView.as_view(),
        name="session_note_create",
    ),
    path(
        "prontuarios/<int:record_pk>/conceder/",
        views.ClinicalRecordGrantAccessView.as_view(),
        name="grant_access",
    ),
    path(
        "prontuarios/<int:record_pk>/revogar/<int:user_pk>/",
        views.ClinicalRecordRevokeAccessView.as_view(),
        name="revoke_access",
    ),
]
