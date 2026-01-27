import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date

from audit.models import AuditEvent
from chat.models import ChatMessage
from documents.models import Document, DocumentShare
from logistics.models import ContainerShipment, ContainerItem

STATUS_LABELS = {"CREATED": "Créé", "IN_TRANSIT": "En transit", "ARRIVED": "Arrivé", "CLEARED": "Dédouané", "DELIVERED": "Livré"}

@login_required
def dashboard(request):
    user = request.user
    if user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE":
        visible = ContainerShipment.objects.all()
    else:
        visible = ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    shipments = list(visible.order_by("-created_at")[:5])
    for s in shipments: s.status_label = STATUS_LABELS.get(s.status, s.status)
    total_val = ContainerItem.objects.filter(shipment__in=visible).aggregate(total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2))))["total"] or 0
    return render(request, "ui/dashboard.html", {"user": user, "shipments": shipments, "total_shipments": visible.count(), "in_transit": visible.filter(status="IN_TRANSIT").count(), "delivered": visible.filter(status="DELIVERED").count(), "total_value": total_val})

@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
    if user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE":
        shipments = ContainerShipment.objects.all()
    else:
        shipments = ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    shipment = get_object_or_404(shipments, pk=shipment_id)
    if request.method == "POST":
        if request.POST.get("form_name") == "chat":
            body = (request.POST.get("body") or "").strip()
            if body: ChatMessage.objects.create(shipment=shipment, author=user, site=user.site or "BE", body=body)
            return redirect(f"/shipments/{shipment_id}/#chat")
    items = shipment.items.select_related("product").all()
    for item in items: item.line_total = item.qty * item.unit_price
    return render(request, "ui/shipment_info.html", {"shipment": shipment, "items": items, "documents": Document.objects.filter(linked_shipment=shipment), "chat_messages": ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")})

@login_required
def shipments_list(request):
    user = request.user
    shipments = ContainerShipment.objects.all() if (user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE") else ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    page_obj = Paginator(shipments.order_by("-created_at"), 20).get_page(request.GET.get("page"))
    for s in page_obj: s.status_label = STATUS_LABELS.get(s.status, s.status)
    return render(request, "ui/shipments_list.html", {"shipments": page_obj, "page_obj": page_obj})

@login_required
def shipment_documents(request, shipment_id: int):
    user = request.user
    shipments = ContainerShipment.objects.all() if (user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE") else ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    shipment = get_object_or_404(shipments, pk=shipment_id)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "share":
            doc_id = request.POST.get("document_id")
            doc = Document.objects.filter(linked_shipment=shipment, pk=doc_id).first()
            if doc:
                share = DocumentShare.objects.create(document=doc, expire_at=timezone.now() + timedelta(days=7), created_by=user)
                return redirect(f"/shipments/{shipment_id}/documents/?shared={share.token}")
        else:
            d_type, f = request.POST.get("doc_type"), request.FILES.get("file")
            if d_type and f:
                ex = Document.objects.filter(linked_shipment=shipment, doc_type=d_type)
                v = (ex.order_by("-version").first().version + 1) if ex.exists() else 1
                ex.update(is_current=False)
                Document.objects.create(linked_shipment=shipment, doc_type=d_type, file=f, uploaded_by=user, version=v, is_current=True)
                messages.success(request, "Document ajouté")
            return redirect(f"/shipments/{shipment_id}/documents/")
    docs = list(Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at"))
    for d in docs: d.can_share = (user.role in ("BOSS", "HQ_ADMIN") or d.uploaded_by_id == user.id or getattr(user, 'site', '') == "BE")
    token = request.GET.get("shared")
    url = request.build_absolute_uri(f"/documents/share/{token}/") if token else None
    return render(request, "ui/shipment_documents.html", {"shipment": shipment, "documents": docs, "share_url": url})

def document_share_view(request, token: str):
    share = DocumentShare.objects.filter(token=token).first()
    if not share or share.expire_at < timezone.now(): return render(request, "ui/document_share_invalid.html", {"message": "Lien expiré"})
    return FileResponse(share.document.file.open("rb"))

def logout_view(request):
    auth_logout(request)
    return redirect("/login/")

class RoleLoginView(LoginView):
    template_name = "ui/login.html"
    def get_success_url(self): return reverse_lazy("dashboard")

@login_required
def profile_view(request):
    return render(request, "ui/profile.html", {"user": request.user})