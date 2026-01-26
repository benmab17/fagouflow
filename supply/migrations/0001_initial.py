from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Supplier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=50)),
                ("address", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.CharField(max_length=100, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("unit", models.CharField(default="unit", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site", models.CharField(choices=[("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SENT", "Sent"), ("RECEIVED", "Received")], default="DRAFT", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("supplier", models.ForeignKey(on_delete=models.CASCADE, related_name="purchase_orders", to="supply.supplier")),
            ],
        ),
        migrations.CreateModel(
            name="PurchaseOrderLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qty", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("product", models.ForeignKey(on_delete=models.PROTECT, to="supply.product")),
                ("purchase_order", models.ForeignKey(on_delete=models.CASCADE, related_name="lines", to="supply.purchaseorder")),
            ],
        ),
    ]