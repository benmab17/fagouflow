import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("supply", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContainerShipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("container_no", models.CharField(max_length=100)),
                ("bl_no", models.CharField(max_length=100)),
                ("status", models.CharField(choices=[("CREATED", "Created"), ("IN_TRANSIT", "In Transit"), ("ARRIVED", "Arrived"), ("CLEARED", "Cleared"), ("DELIVERED", "Delivered")], default="CREATED", max_length=30)),
                ("etd", models.DateField(blank=True, null=True)),
                ("eta", models.DateField(blank=True, null=True)),
                ("origin_country", models.CharField(max_length=100)),
                ("destination_type", models.CharField(choices=[("DIRECT_CLIENT", "Direct Client"), ("BRANCH_STOCK", "Branch Stock")], max_length=30)),
                ("destination_site", models.CharField(blank=True, choices=[("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10, null=True)),
                ("client_name", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ContainerItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.PositiveIntegerField()),
                ("unit", models.CharField(default="unit", max_length=50)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("product", models.ForeignKey(on_delete=models.PROTECT, to="supply.product")),
                ("shipment", models.ForeignKey(on_delete=models.CASCADE, related_name="items", to="logistics.containershipment")),
            ],
        ),
        migrations.CreateModel(
            name="StatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(max_length=30)),
                ("to_status", models.CharField(max_length=30)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("note", models.TextField(blank=True)),
                ("changed_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("shipment", models.ForeignKey(on_delete=models.CASCADE, related_name="status_history", to="logistics.containershipment")),
            ],
        ),
    ]