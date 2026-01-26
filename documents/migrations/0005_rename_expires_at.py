from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0004_document_title"),
    ]

    operations = [
        migrations.RenameField(
            model_name="documentshare",
            old_name="expires_at",
            new_name="expire_at",
        ),
    ]
