from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0005_rename_expires_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentSiteShare",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site", models.CharField(choices=[("BE", "BE"), ("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")], max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="site_shares", to="documents.document"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="documentsiteshare",
            constraint=models.UniqueConstraint(fields=("document", "site"), name="unique_document_site_share"),
        ),
    ]
