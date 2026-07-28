from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("", views.CalendarDayView.as_view(), name="calendar_day"),
    path("novo/", views.AppointmentCreateView.as_view(), name="appointment_create"),
    path("<int:pk>/", views.AppointmentDetailView.as_view(), name="appointment_detail"),
    path("<int:pk>/editar/", views.AppointmentUpdateView.as_view(), name="appointment_update"),
    path("<int:pk>/confirmar/", views.AppointmentConfirmView.as_view(), name="appointment_confirm"),
    path("<int:pk>/checkin/", views.AppointmentCheckInView.as_view(), name="appointment_checkin"),
    path("<int:pk>/concluir/", views.AppointmentCompleteView.as_view(), name="appointment_complete"),
    path("<int:pk>/cancelar/", views.AppointmentCancelView.as_view(), name="appointment_cancel"),
    path(
        "<int:pk>/lista-de-espera/",
        views.WaitListMatchesView.as_view(),
        name="waitlist_matches",
    ),
    path(
        "<int:appointment_pk>/lista-de-espera/<int:waitlist_pk>/preencher/",
        views.WaitListFulfillView.as_view(),
        name="waitlist_fulfill",
    ),
    path("lista-de-espera/", views.WaitListListView.as_view(), name="waitlist_list"),
    path("lista-de-espera/novo/", views.WaitListCreateView.as_view(), name="waitlist_create"),
]
