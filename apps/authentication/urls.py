from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("escolher-empresa/", views.ChooseTenantView.as_view(), name="choose_tenant"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("api/token/", views.TenantTokenObtainPairView.as_view(), name="api_token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
]
