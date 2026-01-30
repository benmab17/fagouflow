from __future__ import annotations

import json
import os
from typing import Dict, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Client, ShipmentUpdate
from documents.models import Document
from logistics.models import ContainerShipment


class Command(BaseCommand):
    help = "Export anonymized Client Portal fixtures to JSON (PREVIEW ONLY)."

    def add_arguments(self, parser):
        parser.add_argument("--client-id", type=int, default=None, help="Limit export to one client id")
        parser.add_argument("--limit", type=int, default=200, help="Max objects per model")
        parser.add_argument("--out", type=str, default="fixtures/client_portal_export.json", help="Output file path")
        parser.add_argument("--include-docs", action="store_true", help="Include Document objects")
        parser.add_argument("--exclude-docs", action="store_true", help="Exclude Document objects (default)")
        parser.add_argument(
            "--extra-exclude",
            action="append",
            default=[],
            help='Extra exclude list per model. Format: "ModelName:field1,field2" (repeatable).',
        )
        parser.add_argument("--no-mask", action="store_true", help="Disable masking (DEV ONLY)")
        parser.add_argument(
            "--only-models",
            type=str,
            default=None,
            help='Export only specific models (comma-separated), e.g. "Client,Container,TrackingEvent"',
        )
        parser.add_argument("--strict", action="store_true", help="Refuse export in PROD-like environments")
        parser.add_argument(
            "--i-know-what-i-am-doing",
            action="store_true",
            help="Override strict mode (DEV ONLY, use with extreme caution)",
        )

    def handle(self, *args, **options):
        include_docs = options["include_docs"]
        exclude_docs = options["exclude_docs"]
        if include_docs and exclude_docs:
            raise CommandError("Choose either --include-docs or --exclude-docs (not both).")
        if not include_docs and not exclude_docs:
            exclude_docs = True

        if options["strict"] and self._is_prod_like() and not options["i_know_what_i_am_doing"]:
            raise CommandError("Strict mode: export refused in PROD-like environment.")
        if options["strict"] and self._is_prod_like() and options["i_know_what_i_am_doing"]:
            self.stdout.write(self.style.WARNING("WARNING: overriding strict PROD protection. DEV ONLY."))

        no_mask = options["no_mask"]
        if no_mask:
            self.stdout.write(self.style.WARNING("WARNING: --no-mask used. DEV ONLY."))

        extra_exclude = self._parse_extra_exclude(options["extra_exclude"])

        only_models = self._parse_only_models(options["only_models"])

        client_id = options["client_id"]
        limit = options["limit"]
        out_path = options["out"]

        clients_qs = Client.objects.all().order_by("id")
        if client_id:
            clients_qs = clients_qs.filter(id=client_id)
        clients = list(clients_qs[:limit])

        client_ids = [c.id for c in clients]

        shipments_qs = ContainerShipment.objects.filter(client_id__in=client_ids).order_by("id")
        shipments = list(shipments_qs[:limit])
        shipment_ids = [s.id for s in shipments]

        documents: List[Document] = []
        if include_docs:
            documents_qs = Document.objects.filter(linked_shipment_id__in=shipment_ids).order_by("id")
            documents = list(documents_qs[:limit])

        updates_qs = ShipmentUpdate.objects.filter(shipment_id__in=shipment_ids).order_by("id")
        updates = list(updates_qs[:limit])

        User = get_user_model()
        users_qs = User.objects.filter(client_id__in=client_ids).order_by("id")
        users = list(users_qs[:limit])

        data: List[Dict] = []
        counts = {"Client": 0, "User": 0, "Container": 0, "TrackingEvent": 0, "Document": 0}

        if "Client" in only_models:
            for c in clients:
                fields = {
                    "name": c.name,
                    "email": f"client{c.pk}@example.com",
                    "phone": "",
                    "country": c.country,
                    "address": "",
                    "created_at": c.created_at.isoformat(),
                }
                fields = self._mask_fields("Client", fields, extra_exclude, no_mask)
                data.append({"model": "core.client", "pk": c.pk, "fields": fields})
                counts["Client"] += 1

        if "User" in only_models:
            for u in users:
                fields = {
                    "email": f"user{u.pk}@example.com",
                    "full_name": f"User {u.pk}",
                    "role": u.role,
                    "site": u.site,
                    "client": u.client_id,
                    "is_active": u.is_active,
                    "is_staff": u.is_staff,
                    "date_joined": u.date_joined.isoformat() if u.date_joined else timezone.now().isoformat(),
                }
                fields = self._mask_fields("User", fields, extra_exclude, no_mask)
                data.append({"model": "accounts.user", "pk": u.pk, "fields": fields})
                counts["User"] += 1

        if "Container" in only_models:
            for s in shipments:
                fields = {
                    "container_no": s.container_no,
                    "bl_no": s.bl_no,
                    "status": s.status,
                    "etd": s.etd.isoformat() if s.etd else None,
                    "eta": s.eta.isoformat() if s.eta else None,
                    "origin_country": s.origin_country,
                    "destination_type": s.destination_type,
                    "destination_site": s.destination_site,
                    "client_name": s.client_name or (s.client.name if s.client_id else ""),
                    "client": s.client_id,
                    "created_by": None,
                    "created_at": s.created_at.isoformat() if s.created_at else timezone.now().isoformat(),
                }
                fields = self._mask_fields("ContainerShipment", fields, extra_exclude, no_mask)
                data.append({"model": "logistics.containershipment", "pk": s.pk, "fields": fields})
                counts["Container"] += 1

        if "Document" in only_models and include_docs:
            for d in documents:
                fields = {
                    "linked_shipment": d.linked_shipment_id,
                    "linked_po": None,
                    "title": d.title or "",
                    "doc_type": d.doc_type,
                    "description": "",
                    "file": d.file.name or "",
                    "uploaded_by": None,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else timezone.now().isoformat(),
                    "version": d.version,
                    "is_current": d.is_current,
                }
                fields = self._mask_fields("Document", fields, extra_exclude, no_mask)
                data.append({"model": "documents.document", "pk": d.pk, "fields": fields})
                counts["Document"] += 1

        if "TrackingEvent" in only_models:
            for u in updates:
                fields = {
                    "shipment": u.shipment_id,
                    "status": u.status,
                    "notes": u.notes or "",
                    "created_by": None,
                    "created_at": u.created_at.isoformat() if u.created_at else timezone.now().isoformat(),
                }
                fields = self._mask_fields("ShipmentUpdate", fields, extra_exclude, no_mask)
                data.append({"model": "core.shipmentupdate", "pk": u.pk, "fields": fields})
                counts["TrackingEvent"] += 1

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        exported = [k for k, v in counts.items() if v > 0]
        self.stdout.write(self.style.SUCCESS("Exported {} records to {}".format(len(data), out_path)))
        self.stdout.write(self.style.SUCCESS("Models exported: {}".format(", ".join(exported) or "none")))
        self.stdout.write(self.style.SUCCESS("Counts: {}".format(counts)))

    def _parse_only_models(self, value: str | None) -> List[str]:
        if not value:
            return ["Client", "User", "Container", "TrackingEvent", "Document"]
        raw = [v.strip() for v in value.split(",") if v.strip()]
        aliases = {
            "Shipment": "Container",
            "ContainerShipment": "Container",
            "Tracking": "TrackingEvent",
            "ShipmentUpdate": "TrackingEvent",
        }
        normalized = []
        for name in raw:
            name = aliases.get(name, name)
            normalized.append(name)
        allowed = {"Client", "User", "Container", "TrackingEvent", "Document"}
        unknown = [n for n in normalized if n not in allowed]
        if unknown:
            raise CommandError("Unknown model(s) in --only-models: {}".format(", ".join(unknown)))
        return normalized

    def _parse_extra_exclude(self, items: List[str]) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for item in items:
            if ":" not in item:
                continue
            model, fields = item.split(":", 1)
            result.setdefault(model, [])
            result[model].extend([f.strip() for f in fields.split(",") if f.strip()])
        return result

    def _mask_fields(self, model: str, fields: Dict, extra_exclude: Dict[str, List[str]], no_mask: bool) -> Dict:
        if no_mask:
            for field in extra_exclude.get(model, []):
                fields.pop(field, None)
            return fields

        default_exclude = {
            "User": ["password", "last_login", "is_superuser", "is_staff"],
            "Client": ["phone", "email"],
            "Document": ["file"],
        }
        for field in default_exclude.get(model, []):
            if field in fields:
                if model == "Client" and field in ("phone", "email"):
                    fields[field] = ""
                elif model == "Document" and field == "file":
                    fields[field] = ""
                else:
                    fields.pop(field, None)
        for field in extra_exclude.get(model, []):
            fields.pop(field, None)
        return fields

    def _is_prod_like(self) -> bool:
        if getattr(settings, "DEBUG", False) is False:
            return True
        env = (os.getenv("DJANGO_ENV") or "").lower()
        if env in ("prod", "production"):
            return True
        hosts = getattr(settings, "ALLOWED_HOSTS", []) or []
        for h in hosts:
            if "render.com" in h or ".com" in h or ".net" in h:
                return True
        return False
