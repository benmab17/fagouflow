from rest_framework import viewsets

from core.permissions import filter_queryset_by_site
from .filters import AuditEventFilter
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all().order_by("-created_at")
    serializer_class = AuditEventSerializer
    filterset_class = AuditEventFilter

    def get_queryset(self):
        return filter_queryset_by_site(AuditEvent.objects.all().order_by("-created_at"), self.request.user, ["site"])