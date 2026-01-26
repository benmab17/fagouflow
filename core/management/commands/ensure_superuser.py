import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a default superuser if it doesn't exist."

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@fagouflow.local")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "Admin123!")
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser created: {email}"))
        else:
            self.stdout.write(f"Superuser already exists: {email}")
