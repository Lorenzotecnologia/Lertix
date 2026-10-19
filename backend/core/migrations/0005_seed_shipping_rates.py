from decimal import Decimal

from django.db import migrations

# Valores iniciais de referência: ajuste em Admin > Tarifas de frete.
REGIONS = [
    ("São Paulo", "SP", [("12.00", 3), ("16.00", 3), ("22.00", 4), ("35.00", 5)], 3),
    ("Sudeste", "RJ,MG,ES", [("16.00", 5), ("20.00", 5), ("28.00", 6), ("45.00", 7)], 5),
    ("Sul", "PR,SC,RS", [("18.00", 6), ("23.00", 6), ("32.00", 7), ("50.00", 8)], 6),
    ("Centro-Oeste", "DF,GO,MT,MS", [("20.00", 7), ("26.00", 7), ("36.00", 8), ("55.00", 9)], 7),
    ("Nordeste", "BA,SE,AL,PE,PB,RN,CE,PI,MA", [("24.00", 8), ("30.00", 8), ("42.00", 10), ("65.00", 12)], 8),
    ("Norte", "AC,AP,AM,PA,RO,RR,TO", [("28.00", 10), ("36.00", 10), ("50.00", 12), ("75.00", 14)], 10),
]
WEIGHTS = [500, 1000, 2000, 5000]


def seed(apps, schema_editor):
    ShippingRate = apps.get_model("core", "ShippingRate")
    for region, states, tiers, _ in REGIONS:
        for weight, (price, days) in zip(WEIGHTS, tiers):
            ShippingRate.objects.create(
                region=region,
                states=states,
                max_weight_grams=weight,
                price=Decimal(price),
                delivery_days=days,
            )


def unseed(apps, schema_editor):
    apps.get_model("core", "ShippingRate").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0004_shipping")]
    operations = [migrations.RunPython(seed, unseed)]
