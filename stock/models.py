from django.db import models
from django.conf import settings

from logistics.models import ContainerShipment
from supply.models import Product


class StockLocation(models.Model):
    SITE_CHOICES = [("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    site = models.CharField(max_length=10, choices=SITE_CHOICES)
    name = models.CharField(max_length=100, default="Main")
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.site} - {self.name}"


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("IN", "In"),
        ("OUT", "Out"),
        ("ADJUSTMENT", "Adjustment"),
    ]
    SITE_CHOICES = [("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    site = models.CharField(max_length=10, choices=SITE_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.IntegerField()
    related_shipment = models.ForeignKey(ContainerShipment, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)


class Sale(models.Model):
    SITE_CHOICES = [("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    site = models.CharField(max_length=10, choices=SITE_CHOICES)
    client_local = models.CharField(max_length=200)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)