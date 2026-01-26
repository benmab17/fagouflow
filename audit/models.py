from django.db import models
from django.conf import settings


class AuditEvent(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("STATUS_CHANGE", "Status Change"),
        ("UPLOAD_DOC", "Upload Document"),
        ("STOCK_MOVE", "Stock Move"),
        ("SALE", "Sale"),
    ]
    SITE_CHOICES = [("BE", "BE"), ("PN", "PN"), ("DLA", "DLA"), ("KIN", "KIN")]

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    site = models.CharField(max_length=10, choices=SITE_CHOICES, blank=True)
    summary = models.CharField(max_length=255)
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type} {self.entity_id}"