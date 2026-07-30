from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.MembershipListView.as_view(), name="membership_list"),
    path("novo/", views.MembershipCreateView.as_view(), name="membership_create"),
    path("<int:pk>/papel/", views.MembershipRoleUpdateView.as_view(), name="membership_role"),
    path("<int:pk>/status/", views.MembershipToggleActiveView.as_view(), name="membership_toggle_active"),
    path("<int:pk>/remover/", views.MembershipDeleteView.as_view(), name="membership_delete"),
]
