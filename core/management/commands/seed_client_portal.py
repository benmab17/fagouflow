from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Client
from logistics.models import ContainerShipment


class Command(BaseCommand):
    help = "Seed minimal Client Portal data (clients, user, shipments)."

    def handle(self, *args, **options):
        User = get_user_model()

        client_a, _ = Client.objects.get_or_create(
            name="Client Alpha",
            defaults={"email": "alpha@client.test", "country": "CM"},
        )
        client_b, _ = Client.objects.get_or_create(
            name="Client Beta",
            defaults={"email": "beta@client.test", "country": "CM"},
        )

        user, created = User.objects.get_or_create(
            email="client.alpha@example.com",
            defaults={
                "full_name": "Client Alpha",
                "role": "CLIENT",
                "site": "BE",
                "client": client_a,
            },
        )
        if created:
            user.set_password("client123")
            user.save(update_fields=["password"])
        else:
            if user.client_id != client_a.id:
                user.client = client_a
                user.save(update_fields=["client"])

        def make_shipment(container_no, bl_no, status, client):
            return ContainerShipment.objects.get_or_create(
                container_no=container_no,
                defaults={
                    "bl_no": bl_no,
                    "status": status,
                    "origin_country": "CM",
                    "destination_type": "DIRECT_CLIENT",
                    "destination_site": "PN",
                    "client_name": client.name,
                    "client": client,
                    "created_by": user,
                    "created_at": timezone.now(),
                },
            )

        make_shipment("CMAU1234567", "BL-ALPHA-001", "IN_TRANSIT", client_a)
        make_shipment("CMAU7654321", "BL-ALPHA-002", "CREATED", client_a)
        make_shipment("MSCU9999999", "BL-BETA-001", "DELIVERED", client_b)

        self.stdout.write(self.style.SUCCESS("Client Portal seed complete."))
