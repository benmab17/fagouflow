from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, List

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from chat.models import ChatMessage
from documents.models import Document
from logistics.models import ContainerShipment


@dataclass
class AlertItem:
    level: str
    title: str
    message: str
    shipment_id: int
    container_code: str
    url: str


def _setting(name: str, default):
    return getattr(settings, name, default)


def build_alerts(visible_shipments: Iterable[ContainerShipment]) -> List[AlertItem]:
    max_alerts = int(_setting("ALERTS_MAX_ITEMS", 10))
    transit_days = int(_setting("ALERTS_TRANSIT_DAYS", 7))
    required_docs = list(_setting("ALERTS_REQUIRED_DOC_TYPES", ["BL", "INVOICE"]))

    alerts: List[AlertItem] = []
    today = timezone.now().date()

    try:
        late_qs = (
            visible_shipments.filter(status="IN_TRANSIT", created_at__lt=today - timedelta(days=transit_days))
            .order_by("created_at")[:max_alerts]
        )
        for s in late_qs:
            alerts.append(AlertItem(
                level="critical",
                title="Retard en transit",
                message=f"En transit depuis plus de {transit_days} jours",
                shipment_id=s.id,
                container_code=s.container_no,
                url=f"/shipments/{s.id}/",
            ))
    except Exception:
        pass

    try:
        missing_dest = (
            visible_shipments.filter(Q(destination_site__isnull=True) | Q(destination_site=""))
            .order_by("-created_at")[:max_alerts]
        )
        for s in missing_dest:
            alerts.append(AlertItem(
                level="important",
                title="Destination manquante",
                message="Aucun site de destination",
                shipment_id=s.id,
                container_code=s.container_no,
                url=f"/shipments/{s.id}/",
            ))
    except Exception:
        pass

    try:
        if required_docs:
            doc_qs = Document.objects.filter(linked_shipment__in=visible_shipments, doc_type__in=required_docs)
            doc_ids = set(doc_qs.values_list("linked_shipment_id", "doc_type"))
            for s in visible_shipments.order_by("-created_at")[:max_alerts]:
                missing = [d for d in required_docs if (s.id, d) not in doc_ids]
                if missing:
                    alerts.append(AlertItem(
                        level="important",
                        title="Documents manquants",
                        message=f"Manquants: {', '.join(missing)}",
                        shipment_id=s.id,
                        container_code=s.container_no,
                        url=f"/shipments/{s.id}/",
                    ))
    except Exception:
        pass

    try:
        if "is_read" in {f.name for f in ChatMessage._meta.get_fields()}:
            unread = (
                ChatMessage.objects.filter(shipment__in=visible_shipments, is_read=False)
                .select_related("shipment")
                .order_by("-created_at")[:max_alerts]
            )
            for m in unread:
                alerts.append(AlertItem(
                    level="info",
                    title="Message non lu",
                    message="Nouveau message",
                    shipment_id=m.shipment_id,
                    container_code=getattr(m.shipment, "container_no", ""),
                    url=f"/shipments/{m.shipment_id}/#chat",
                ))
    except Exception:
        pass

    level_rank = {"critical": 0, "important": 1, "info": 2}
    alerts_sorted = sorted(alerts, key=lambda a: level_rank.get(a.level, 9))
    return alerts_sorted[:max_alerts]
