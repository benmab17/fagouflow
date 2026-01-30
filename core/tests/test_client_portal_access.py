from django.test import TestCase
from django.contrib.auth import get_user_model

from logistics.models import ContainerShipment


class ClientPortalAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="pass1234",
            full_name="Client A",
            role="CLIENT",
            site="BE",
        )
        self.internal_user = User.objects.create_user(
            email="boss@example.com",
            password="pass1234",
            full_name="Boss",
            role="BOSS",
            site="BE",
            is_staff=True,
        )
        self.client_shipment = ContainerShipment.objects.create(
            container_no="C001",
            bl_no="BL001",
            status="IN_TRANSIT",
            origin_country="FR",
            destination_type="DIRECT_CLIENT",
            destination_site="BE",
            client_name="Client A",
            created_by=self.internal_user,
        )
        self.other_shipment = ContainerShipment.objects.create(
            container_no="C002",
            bl_no="BL002",
            status="IN_TRANSIT",
            origin_country="FR",
            destination_type="DIRECT_CLIENT",
            destination_site="BE",
            client_name="Client B",
            created_by=self.internal_user,
        )

    def test_client_access_own_shipment(self):
        self.client.force_login(self.client_user)
        res = self.client.get(f"/client/containers/{self.client_shipment.id}/")
        self.assertEqual(res.status_code, 200)

    def test_client_access_other_shipment_404(self):
        self.client.force_login(self.client_user)
        res = self.client.get(f"/client/containers/{self.other_shipment.id}/")
        self.assertEqual(res.status_code, 404)

    def test_client_redirects_from_direction(self):
        self.client.force_login(self.client_user)
        res = self.client.get("/direction/")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res["Location"].endswith("/client/"))

    def test_internal_redirects_from_client_portal(self):
        self.client.force_login(self.internal_user)
        res = self.client.get("/client/")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res["Location"].endswith("/dashboard/"))
