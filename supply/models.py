from django.db import models
from django.conf import settings


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name or self.contact_email or f"Supplier #{self.pk}"


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, default="unit")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        sku = self.sku or ""
        name = self.name or ""
        label = f"{sku} - {name}".strip(" -")
        return label or f"Product #{self.pk}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SENT", "Sent"),
        ("RECEIVED", "Received"),
    ]
    SITE_CHOICES = [("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    site = models.CharField(max_length=10, choices=SITE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
