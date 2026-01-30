from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_client"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="preview_only",
            field=models.BooleanField(default=False),
        ),
    ]
