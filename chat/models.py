from django.conf import settings
from django.db import models

from logistics.models import ContainerShipment


class ChatMessage(models.Model):
    shipment = models.ForeignKey(
        ContainerShipment,
        related_name="chat_messages",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    site = models.CharField(max_length=10, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Msg {self.pk} - {self.shipment.container_no}"
