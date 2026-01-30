from django.conf import settings
from django.db import models

from logistics.models import ContainerShipment


class ShipmentUpdate(models.Model):
    shipment = models.ForeignKey(
        ContainerShipment, on_delete=models.CASCADE, related_name="updates"
    )
    status = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        shipment_ref = ""
        try:
            shipment_ref = self.shipment.container_no if self.shipment_id and self.shipment else ""
        except Exception:
            shipment_ref = ""
        return shipment_ref or f"Update #{self.pk}"


class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    preview_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name or self.email or f"Client #{self.pk}"
