from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_clientchatmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientchatmessage",
            name="sender_type",
            field=models.CharField(default="client", max_length=10),
        ),
    ]
