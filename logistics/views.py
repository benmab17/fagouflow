from rest_framework import viewsets

from core.permissions import filter_queryset_by_site
from .filters import ShipmentFilter
from .models import ContainerShipment, ContainerItem, StatusHistory
from .serializers import ContainerShipmentSerializer, ContainerItemSerializer, StatusHistorySerializer


class ContainerShipmentViewSet(viewsets.ModelViewSet):
    queryset = ContainerShipment.objects.all()
    serializer_class = ContainerShipmentSerializer
    filterset_class = ShipmentFilter

    def get_queryset(self):
        return filter_queryset_by_site(ContainerShipment.objects.all(), self.request.user, ["destination_site"])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContainerItemViewSet(viewsets.ModelViewSet):
    queryset = ContainerItem.objects.all()
    serializer_class = ContainerItemSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"BOSS", "HQ_ADMIN"}:
            return ContainerItem.objects.all()
        return ContainerItem.objects.filter(shipment__destination_site=user.site)


class StatusHistoryViewSet(viewsets.ModelViewSet):
    queryset = StatusHistory.objects.all()
    serializer_class = StatusHistorySerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"BOSS", "HQ_ADMIN"}:
            return StatusHistory.objects.all()
        return StatusHistory.objects.filter(shipment__destination_site=user.site)

    def perform_create(self, serializer):
        serializer.save(changed_by=self.request.user)
