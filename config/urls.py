from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import UserViewSet
from supply.views import SupplierViewSet, ProductViewSet, PurchaseOrderViewSet, PurchaseOrderLineViewSet
from logistics.views import ContainerShipmentViewSet, ContainerItemViewSet, StatusHistoryViewSet
from documents.views import DocumentViewSet
from stock.views import StockLocationViewSet, StockMovementViewSet, SaleViewSet, SaleLineViewSet
from audit.views import AuditEventViewSet
from reports.views import AuditReportViewSet
from django.conf import settings
from django.conf.urls.static import static

from core.views import RoleLoginView, dashboard, document_share_view, logout_view, profile_view, reports_view, shipment_detail, shipment_documents, shipments_list

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchaseorder")
router.register(r"purchase-order-lines", PurchaseOrderLineViewSet, basename="purchaseorderline")
router.register(r"shipments", ContainerShipmentViewSet, basename="shipment")
router.register(r"shipment-items", ContainerItemViewSet, basename="shipmentitem")
router.register(r"shipment-status", StatusHistoryViewSet, basename="statushistory")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"stock-locations", StockLocationViewSet, basename="stocklocation")
router.register(r"stock-movements", StockMovementViewSet, basename="stockmovement")
router.register(r"sales", SaleViewSet, basename="sale")
router.register(r"sale-lines", SaleLineViewSet, basename="saleline")
router.register(r"audit-events", AuditEventViewSet, basename="auditevent")
router.register(r"reports/audit", AuditReportViewSet, basename="auditreport")

urlpatterns = [
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    path("admin/", admin.site.urls),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("dashboard/", dashboard, name="dashboard"),
    path("shipments/", shipments_list, name="shipments_list"),
    path("shipments/<int:shipment_id>/", shipment_detail, name="shipment_detail"),
    path("shipments/<int:shipment_id>/documents/", shipment_documents, name="shipment_documents"),
    path("reports/", reports_view, name="reports"),
    path("documents/share/<str:token>/", document_share_view, name="document_share_view"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
    path("accounts/login/", RedirectView.as_view(url="/login/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
