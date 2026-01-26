from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from supply.models import Supplier, Product, PurchaseOrder, PurchaseOrderLine
from logistics.models import ContainerShipment, ContainerItem, StatusHistory
from documents.models import Document
from stock.models import StockLocation, StockMovement, Sale, SaleLine


class Command(BaseCommand):
    help = "Seed demo data"

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(self.style.WARNING("Users already exist, skipping seed."))
            return

        boss = User.objects.create_user("boss@fagouflow.local", "password", full_name="Boss", role="BOSS", site="BE", is_staff=True)
        hq1 = User.objects.create_user("hq1@fagouflow.local", "password", full_name="HQ One", role="HQ_ADMIN", site="BE", is_staff=True)
        hq2 = User.objects.create_user("hq2@fagouflow.local", "password", full_name="HQ Two", role="HQ_ADMIN", site="BE", is_staff=True)
        pn = User.objects.create_user("agentpn@fagouflow.local", "password", full_name="Agent PN", role="BRANCH_AGENT", site="PN")
        dla = User.objects.create_user("agentdla@fagouflow.local", "password", full_name="Agent DLA", role="BRANCH_AGENT", site="DLA")
        kin = User.objects.create_user("agentkin@fagouflow.local", "password", full_name="Agent KIN", role="BRANCH_AGENT", site="KIN")

        supplier = Supplier.objects.create(name="Global Supplier", contact_email="contact@supplier.local")
        product_a = Product.objects.create(sku="SKU-001", name="Widget A", unit="box")
        product_b = Product.objects.create(sku="SKU-002", name="Widget B", unit="unit")

        po = PurchaseOrder.objects.create(supplier=supplier, site="PN", created_by=pn, status="SENT")
        PurchaseOrderLine.objects.create(purchase_order=po, product=product_a, qty=10, unit_price=100)
        PurchaseOrderLine.objects.create(purchase_order=po, product=product_b, qty=5, unit_price=50)

        shipment1 = ContainerShipment.objects.create(
            container_no="CONT-001",
            bl_no="BL-001",
            status="CREATED",
            etd=timezone.now().date(),
            eta=timezone.now().date(),
            origin_country="CN",
            destination_type="BRANCH_STOCK",
            destination_site="PN",
            created_by=pn,
        )
        ContainerItem.objects.create(shipment=shipment1, product=product_a, qty=100, unit="box", unit_price=90)

        shipment2 = ContainerShipment.objects.create(
            container_no="CONT-002",
            bl_no="BL-002",
            status="IN_TRANSIT",
            etd=timezone.now().date(),
            eta=timezone.now().date(),
            origin_country="TR",
            destination_type="BRANCH_STOCK",
            destination_site="DLA",
            created_by=dla,
        )
        ContainerItem.objects.create(shipment=shipment2, product=product_b, qty=200, unit="unit", unit_price=40)

        shipment3 = ContainerShipment.objects.create(
            container_no="CONT-003",
            bl_no="BL-003",
            status="ARRIVED",
            etd=timezone.now().date(),
            eta=timezone.now().date(),
            origin_country="US",
            destination_type="DIRECT_CLIENT",
            client_name="Local Client",
            created_by=kin,
        )

        StatusHistory.objects.create(shipment=shipment1, from_status="CREATED", to_status="IN_TRANSIT", changed_by=pn, note="Departed")
        shipment1.status = "IN_TRANSIT"
        shipment1.save(update_fields=["status"])
        StatusHistory.objects.create(shipment=shipment1, from_status="IN_TRANSIT", to_status="ARRIVED", changed_by=pn, note="Arrived")
        shipment1.status = "ARRIVED"
        shipment1.save(update_fields=["status"])

        doc_content = ContentFile(b"demo document", name="demo.txt")
        Document.objects.create(linked_shipment=shipment1, doc_type="BL", file=doc_content, uploaded_by=pn)

        StockLocation.objects.create(site="PN", name="Main")
        StockLocation.objects.create(site="DLA", name="Main")
        StockLocation.objects.create(site="KIN", name="Main")

        StockMovement.objects.create(movement_type="IN", site="PN", product=product_a, qty=50, related_shipment=shipment1, created_by=pn)
        sale = Sale.objects.create(site="PN", client_local="Retail Client", created_by=pn)
        SaleLine.objects.create(sale=sale, product=product_a, qty=2, unit_price=120)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
