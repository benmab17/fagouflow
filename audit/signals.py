from __future__ import annotations

import json
from typing import Optional

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.middleware import get_current_user, get_client_ip, get_user_agent
from logistics.models import StatusHistory, ContainerShipment
from documents.models import Document
from supply.models import PurchaseOrder
from stock.models import StockMovement, Sale
from .models import AuditEvent
from .utils import serialize_instance


TRACKED_MODELS = (PurchaseOrder, ContainerShipment, Document, StockMovement, Sale)


def _json_safe(value):
    if value is None:
        return None
    return json.loads(json.dumps(value, default=str))


def _resolve_site(instance) -> str:
    if hasattr(instance, "site"):
        return getattr(instance, "site") or ""
    if hasattr(instance, "destination_site"):
        return getattr(instance, "destination_site") or ""
    if hasattr(instance, "shipment") and hasattr(instance.shipment, "destination_site"):
        return instance.shipment.destination_site or ""
    if hasattr(instance, "linked_shipment") and instance.linked_shipment:
        return instance.linked_shipment.destination_site or ""
    if hasattr(instance, "linked_po") and instance.linked_po:
        return instance.linked_po.site or ""
    return ""


def _create_audit(action: str, instance, before_json: Optional[dict], after_json: Optional[dict], summary: str):
    user = get_current_user()
    AuditEvent.objects.create(
        actor=user,
        action=action,
        entity_type=instance.__class__.__name__,
        entity_id=str(instance.pk),
        site=_resolve_site(instance),
        summary=summary,
        before_json=_json_safe(before_json),
        after_json=_json_safe(after_json),
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
    )


@receiver(pre_save)
def capture_pre_save(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._pre_save_snapshot = serialize_instance(old_instance)
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None


@receiver(post_save)
def create_or_update_audit(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    before_json = getattr(instance, "_pre_save_snapshot", None)
    after_json = serialize_instance(instance)
    if created:
        _create_audit("CREATE", instance, None, after_json, f"Created {sender.__name__} {instance.pk}")
    else:
        _create_audit("UPDATE", instance, before_json, after_json, f"Updated {sender.__name__} {instance.pk}")


@receiver(pre_delete)
def create_delete_audit(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    before_json = serialize_instance(instance)
    _create_audit("DELETE", instance, before_json, None, f"Deleted {sender.__name__} {instance.pk}")


@receiver(post_save, sender=StatusHistory)
def status_change_audit(sender, instance, created, **kwargs):
    if not created:
        return
    summary = f"Shipment {instance.shipment_id} status {instance.from_status} -> {instance.to_status}"
    _create_audit("STATUS_CHANGE", instance.shipment, None, None, summary)


@receiver(post_save, sender=Document)
def upload_doc_audit(sender, instance, created, **kwargs):
    if not created:
        return
    summary = f"Uploaded document {instance.pk} ({instance.doc_type})"
    _create_audit("UPLOAD_DOC", instance, None, None, summary)


@receiver(post_save, sender=StockMovement)
def stock_move_audit(sender, instance, created, **kwargs):
    if not created:
        return
    summary = f"Stock movement {instance.pk} {instance.movement_type}"
    _create_audit("STOCK_MOVE", instance, None, None, summary)


@receiver(post_save, sender=Sale)
def sale_audit(sender, instance, created, **kwargs):
    if not created:
        return
    summary = f"Sale {instance.pk} ({instance.site})"
    _create_audit("SALE", instance, None, None, summary)
