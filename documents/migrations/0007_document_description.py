from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0006_documentsiteshare"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
