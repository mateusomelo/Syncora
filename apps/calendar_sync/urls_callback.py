from django.urls import path

from . import views

app_name = "calendar_sync_callback"

urlpatterns = [
    path("<str:provider>/callback/", views.CalendarCallbackView.as_view(), name="oauth_callback"),
]
