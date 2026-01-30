import uuid
from django.db import models
from django.conf import settings

from supply.models import Product

class ContainerShipment(models.Model):
    STATUS_CHOICES = [
        ("CREATED", "Created"),
        ("IN_TRANSIT", "In Transit"),
        ("ARRIVED", "Arrived"),
        ("CLEARED", "Cleared"),
        ("DELIVERED", "Delivered"),
    ]
    DESTINATION_TYPE_CHOICES = [
        ("DIRECT_CLIENT", "Direct Client"),
        ("BRANCH_STOCK", "Branch Stock"),
    ]
    SITE_CHOICES = [("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    container_no = models.CharField(max_length=100)
    bl_no = models.CharField(max_length=100)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="CREATED")
    etd = models.DateField(null=True, blank=True)
    eta = models.DateField(null=True, blank=True)
    origin_country = models.CharField(max_length=100)
    destination_type = models.CharField(max_length=30, choices=DESTINATION_TYPE_CHOICES)
    destination_site = models.CharField(max_length=10, choices=SITE_CHOICES, null=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    client = models.ForeignKey("core.Client", on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.container_no or self.bl_no or f"Shipment #{self.pk}"


class ContainerItem(models.Model):
    shipment = models.ForeignKey(ContainerShipment, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, default="unit")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        shipment_ref = ""
        product_name = ""
        try:
            shipment_ref = self.shipment.container_no if self.shipment_id and self.shipment else ""
        except Exception:
            shipment_ref = ""
        try:
            product_name = self.product.name if self.product_id and self.product else ""
        except Exception:
            product_name = ""
        qty = self.qty if self.qty is not None else ""
        label = f"{shipment_ref} - {product_name} ({qty})".strip(" -()")
        return label or f"Item #{self.pk}"




class StatusHistory(models.Model):
    shipment = models.ForeignKey(ContainerShipment, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
