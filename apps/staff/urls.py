from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("", views.ProfessionalListView.as_view(), name="list"),
    path("novo/", views.ProfessionalCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ProfessionalDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ProfessionalUpdateView.as_view(), name="update"),
    path("<int:pk>/remover/", views.ProfessionalDeleteView.as_view(), name="delete"),
    path("<int:pk>/horarios/", views.WorkingHoursUpdateView.as_view(), name="working_hours"),
]
