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

from core.views import ClientLoginView, RoleLoginView, dashboard, dashboard_export, direction_view, document_share_view, healthz, logout_view, profile_view, reports_view, shipment_detail, shipment_documents, shipments_list
from core.views import (
    client_portal,
    dashboard_client,
    containers_list,
    container_detail,
    preview_client_dashboard,
    client_container_documents,
    client_container_history,
    client_container_chat,
)

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
    path("healthz", healthz, name="healthz"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("client/login/", ClientLoginView.as_view(), name="client_login"),
    path("client/login/", RedirectView.as_view(url="/login/", permanent=False)),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/export.csv", dashboard_export, name="dashboard_export"),
    path("direction/", direction_view, name="direction"),
    path("shipments/", shipments_list, name="shipments_list"),
    path("shipments/<int:shipment_id>/", shipment_detail, name="shipment_detail"),
    path("shipments/<int:shipment_id>/documents/", shipment_documents, name="shipment_documents"),
    path("client/", client_portal, name="client_portal"),
    path("client/dashboard/", dashboard_client, name="client_dashboard"),
    path("client/containers/", containers_list, name="client_containers_list"),
    path("client/containers/<int:id>/", container_detail, name="client_container_detail"),
    path("client/containers/<int:id>/documents/", client_container_documents, name="client_container_documents"),
    path("client/containers/<int:id>/history/", client_container_history, name="client_container_history"),
    path("client/containers/<int:id>/chat/", client_container_chat, name="client_container_chat"),
    path("reports/", reports_view, name="reports"),
    path("documents/share/<str:token>/", document_share_view, name="document_share_view"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
    path("accounts/login/", RedirectView.as_view(url="/login/", permanent=False)),
]

# Serve media/static in dev; Cloudinary handles media in prod.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path("preview/client-dashboard/", preview_client_dashboard, name="preview_client_dashboard"),
    ]
