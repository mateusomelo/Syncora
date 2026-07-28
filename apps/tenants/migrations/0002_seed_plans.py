from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("tenants", "Plan")
    plans = [
        {
            "name": "Básico",
            "slug": "basico",
            "max_users": 3,
            "max_professionals": 2,
            "max_appointments_per_month": 200,
            "price": "49.90",
        },
        {
            "name": "Profissional",
            "slug": "profissional",
            "max_users": 10,
            "max_professionals": 8,
            "max_appointments_per_month": 1000,
            "price": "149.90",
        },
        {
            "name": "Premium",
            "slug": "premium",
            "max_users": 50,
            "max_professionals": 40,
            "max_appointments_per_month": 10000,
            "price": "349.90",
        },
    ]
    for data in plans:
        Plan.objects.get_or_create(slug=data["slug"], defaults=data)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("tenants", "Plan")
    Plan.objects.filter(slug__in=["basico", "profissional", "premium"]).delete()


class Migration(migrations.Migration):
    dependencies = [("tenants", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, unseed_plans)]
