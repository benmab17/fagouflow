from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_documentshare"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="document",
            name="is_current",
            field=models.BooleanField(default=True),
        ),
    ]
