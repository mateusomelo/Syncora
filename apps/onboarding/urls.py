from django.urls import path

from . import views

app_name = "onboarding"

urlpatterns = [
    path("cadastro/", views.SignupView.as_view(), name="signup"),
    path("cadastro/sucesso/", views.SignupSuccessView.as_view(), name="signup_success"),
]
