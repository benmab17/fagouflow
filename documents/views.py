from rest_framework import viewsets
from django.db.models import Q

from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"BOSS", "HQ_ADMIN"}:
            return Document.objects.all()
        return Document.objects.filter(
            Q(linked_shipment__destination_site=user.site) | Q(linked_po__site=user.site)
        )

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
