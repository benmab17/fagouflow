from django.utils import timezone
from rest_framework import status

from audit.models import AuditEvent


def test_shipment_creates_audit(api_client, boss_user):
    api_client.force_authenticate(user=boss_user)
    payload = {
        "container_no": "CONT-100",
        "bl_no": "BL-100",
        "status": "CREATED",
        "etd": timezone.now().date().isoformat(),
        "eta": timezone.now().date().isoformat(),
        "origin_country": "CN",
        "destination_type": "BRANCH_STOCK",
        "destination_site": "PN",
        "client_name": "",
    }
    response = api_client.post("/api/shipments/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert AuditEvent.objects.filter(action="CREATE", entity_type="ContainerShipment").exists()


def test_report_daily_accessible_to_boss(api_client, boss_user):
    api_client.force_authenticate(user=boss_user)
    date_str = timezone.now().date().isoformat()
    response = api_client.get(f"/api/reports/audit/daily?date={date_str}")
    assert response.status_code == status.HTTP_200_OK
