from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0003_document_versioning"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="title",
            field=models.CharField(default="", max_length=255),
        ),
    ]
