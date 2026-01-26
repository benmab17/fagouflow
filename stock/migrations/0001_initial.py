from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("logistics", "0001_initial"),
        ("supply", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site", models.CharField(choices=[("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("name", models.CharField(default="Main", max_length=100)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Sale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site", models.CharField(choices=[("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("client_local", models.CharField(max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("IN", "In"), ("OUT", "Out"), ("ADJUSTMENT", "Adjustment")], max_length=20)),
                ("site", models.CharField(choices=[("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("qty", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("note", models.TextField(blank=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=models.PROTECT, to="supply.product")),
                ("related_shipment", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to="logistics.containershipment")),
            ],
        ),
        migrations.CreateModel(
            name="SaleLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("product", models.ForeignKey(on_delete=models.PROTECT, to="supply.product")),
                ("sale", models.ForeignKey(on_delete=models.CASCADE, related_name="lines", to="stock.sale")),
            ],
        ),
    ]