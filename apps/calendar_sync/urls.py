from django.urls import path

from . import views

app_name = "calendar_sync"

urlpatterns = [
    path(
        "profissionais/<int:professional_pk>/calendario/",
        views.ProfessionalCalendarView.as_view(),
        name="professional_calendar",
    ),
    path(
        "profissionais/<int:professional_pk>/calendario/<str:provider>/conectar/",
        views.CalendarConnectView.as_view(),
        name="connect",
    ),
    path(
        "profissionais/<int:professional_pk>/calendario/<int:pk>/desconectar/",
        views.CalendarDisconnectView.as_view(),
        name="disconnect",
    ),
    path(
        "profissionais/<int:professional_pk>/calendario/<int:pk>/direcao/",
        views.CalendarSyncDirectionView.as_view(),
        name="sync_direction",
    ),
]
