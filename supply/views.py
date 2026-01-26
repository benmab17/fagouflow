from rest_framework import viewsets

from core.permissions import filter_queryset_by_site
from .models import Supplier, Product, PurchaseOrder, PurchaseOrderLine
from .serializers import SupplierSerializer, ProductSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):
        return filter_queryset_by_site(PurchaseOrder.objects.all(), self.request.user, ["site"])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PurchaseOrderLineViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderLine.objects.all()
    serializer_class = PurchaseOrderLineSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in {"BOSS", "HQ_ADMIN"}:
            return PurchaseOrderLine.objects.all()
        return PurchaseOrderLine.objects.filter(purchase_order__site=user.site)
