from django.urls import path

from . import views

app_name = "branding"

urlpatterns = [
    path("", views.BrandingSettingsView.as_view(), name="settings"),
]
