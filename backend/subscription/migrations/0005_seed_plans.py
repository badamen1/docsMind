from django.db import migrations


PLANS = [
    {
        "plan_type": "free",
        "name": "Free",
        "price": "0.00",
        "description": "Acceso básico: hasta 5 documentos y 10 MB de almacenamiento.",
        "max_documents": 5,
        "max_storage_mb": 10,
    },
    {
        "plan_type": "pro",
        "name": "Pro",
        "price": "9.99",
        "description": "Acceso avanzado: hasta 100 documentos y 1 GB de almacenamiento.",
        "max_documents": 100,
        "max_storage_mb": 1024,
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("subscription", "Plan")
    for data in PLANS:
        Plan.objects.get_or_create(plan_type=data["plan_type"], defaults=data)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("subscription", "Plan")
    Plan.objects.filter(plan_type__in=["free", "pro"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("subscription", "0004_subscription_stripe_customer_id_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_code=unseed_plans),
    ]
