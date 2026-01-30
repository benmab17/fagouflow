import os

from django.db import models
from django.conf import settings
from django.utils.text import get_valid_filename, slugify

from logistics.models import ContainerShipment
from supply.models import PurchaseOrder


def document_upload_path(instance, filename: str) -> str:
    raw_type = (instance.doc_type or "documents").strip()
    safe_type = slugify(raw_type) or "documents"
    base, ext = os.path.splitext(filename or "")
    safe_base = slugify(get_valid_filename(base)) or "document"
    safe_ext = (ext or "").lower()
    safe_name = f"{safe_base}{safe_ext}"
    return f"documents/{safe_type}/{safe_name}"


def generate_share_token() -> str:
    import secrets

    return secrets.token_urlsafe(32)


class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ("BL", "Bill of Lading"),
        ("INVOICE", "Invoice"),
        ("PACKING_LIST", "Packing List"),
        ("CUSTOMS", "Customs"),
        ("PHOTO", "Photo"),
        ("OTHER", "Other"),
    ]

    linked_shipment = models.ForeignKey(ContainerShipment, on_delete=models.SET_NULL, null=True, blank=True)
    linked_po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, default="")
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)


class DocumentShare(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="shares")
    token = models.CharField(max_length=128, unique=True, default=generate_share_token)
    expire_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentSiteShare(models.Model):
    SITE_CHOICES = [("BE", "BE"), ("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="site_shares")
    site = models.CharField(max_length=10, choices=SITE_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "site"], name="unique_document_site_share"),
        ]
