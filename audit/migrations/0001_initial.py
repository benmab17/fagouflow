from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("CREATE", "Create"), ("UPDATE", "Update"), ("DELETE", "Delete"), ("STATUS_CHANGE", "Status Change"), ("UPLOAD_DOC", "Upload Document"), ("STOCK_MOVE", "Stock Move"), ("SALE", "Sale")], max_length=30)),
                ("entity_type", models.CharField(max_length=100)),
                ("entity_id", models.CharField(max_length=100)),
                ("site", models.CharField(blank=True, choices=[("BE", "BE"), ("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("summary", models.CharField(max_length=255)),
                ("before_json", models.JSONField(blank=True, null=True)),
                ("after_json", models.JSONField(blank=True, null=True)),
                ("ip_address", models.CharField(blank=True, max_length=100)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]