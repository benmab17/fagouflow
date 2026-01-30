from __future__ import annotations

import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Client, ShipmentUpdate
from documents.models import Document
from logistics.models import ContainerShipment


class Command(BaseCommand):
    help = "Clear preview-only data (PREVIEW ONLY – DO NOT USE IN PROD)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--older-than-days",
            type=int,
            default=7,
            help="Delete preview-only data older than N days (default: 7).",
        )

    def handle(self, *args, **options):
        env = (os.getenv("DJANGO_ENV") or "").lower()
        if getattr(settings, "DEBUG", False) is False or env in ("prod", "production"):
            raise CommandError("Refusing to run in PROD. Set DEBUG=True and DJANGO_ENV not prod.")

        older_than_days = options["older_than_days"]
        cutoff = timezone.now() - timedelta(days=older_than_days)

        preview_clients = Client.objects.filter(preview_only=True, created_at__lt=cutoff)
        preview_client_ids = list(preview_clients.values_list("id", flat=True))

        docs_qs = Document.objects.filter(linked_shipment__client_id__in=preview_client_ids)
        updates_qs = ShipmentUpdate.objects.filter(shipment__client_id__in=preview_client_ids)
        shipments_qs = ContainerShipment.objects.filter(client_id__in=preview_client_ids)

        docs_count = docs_qs.count()
        updates_count = updates_qs.count()
        shipments_count = shipments_qs.count()
        clients_count = preview_clients.count()

        if getattr(settings, "DEBUG", False) is True:
            self.stdout.write("Preview-only delete summary:")
            self.stdout.write(f"- Clients: {clients_count}")
            self.stdout.write(f"- Shipments: {shipments_count}")
            self.stdout.write(f"- Tracking events: {updates_count}")
            self.stdout.write(f"- Documents: {docs_count}")
            self.stdout.write(f"Older than (days): {older_than_days}")
            confirm = input("Type YES to confirm deletion: ").strip()
            if confirm != "YES":
                self.stdout.write(self.style.WARNING("Aborted. No data deleted."))
                return

        docs_qs.delete()
        updates_qs.delete()
        shipments_qs.delete()
        preview_clients.delete()

        self.stdout.write(self.style.SUCCESS(f"Documents deleted: {docs_count}"))
        self.stdout.write(self.style.SUCCESS(f"Tracking events deleted: {updates_count}"))
        self.stdout.write(self.style.SUCCESS(f"Shipments deleted: {shipments_count}"))
        self.stdout.write(self.style.SUCCESS(f"Clients deleted: {clients_count}"))
        self.stdout.write(self.style.SUCCESS("Preview data cleaned successfully"))
