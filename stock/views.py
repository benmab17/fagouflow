from rest_framework import viewsets

from core.permissions import filter_queryset_by_site
from .models import StockLocation, StockMovement, Sale, SaleLine
from .serializers import StockLocationSerializer, StockMovementSerializer, SaleSerializer, SaleLineSerializer


class StockLocationViewSet(viewsets.ModelViewSet):
    queryset = StockLocation.objects.all()
    serializer_class = StockLocationSerializer

    def get_queryset(self):
        return filter_queryset_by_site(StockLocation.objects.all(), self.request.user, ["site"])


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        return filter_queryset_by_site(StockMovement.objects.all(), self.request.user, ["site"])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def get_queryset(self):
        return filter_queryset_by_site(Sale.objects.all(), self.request.user, ["site"])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SaleLineViewSet(viewsets.ModelViewSet):
    queryset = SaleLine.objects.all()
    serializer_class = SaleLineSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"BOSS", "HQ_ADMIN"}:
            return SaleLine.objects.all()
        return SaleLine.objects.filter(sale__site=user.site)
