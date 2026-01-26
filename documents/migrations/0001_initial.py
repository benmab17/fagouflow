from django.conf import settings
from django.db import migrations, models
import documents.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("logistics", "0001_initial"),
        ("supply", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("doc_type", models.CharField(choices=[("BL", "Bill of Lading"), ("INVOICE", "Invoice"), ("PACKING_LIST", "Packing List"), ("CUSTOMS", "Customs"), ("PHOTO", "Photo"), ("OTHER", "Other")], max_length=30)),
                ("file", models.FileField(upload_to=documents.models.document_upload_path)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("linked_po", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to="supply.purchaseorder")),
                ("linked_shipment", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to="logistics.containershipment")),
                ("uploaded_by", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]