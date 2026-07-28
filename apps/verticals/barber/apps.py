from django.apps import AppConfig


class BarberConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.verticals.barber"
    label = "barber"
    verbose_name = "Vertical: Barbearia"
