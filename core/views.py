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

# Import de tes modèles
from chat.models import ChatMessage
from documents.models import Document, DocumentShare
from logistics.models import ContainerShipment, ContainerItem

STATUS_LABELS = {"CREATED": "Créé", "IN_TRANSIT": "En transit", "ARRIVED": "Arrivé", "CLEARED": "Dédouané", "DELIVERED": "Livré"}

@login_required
def dashboard(request):
    user = request.user
    is_privileged = user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE"
    visible = ContainerShipment.objects.all() if is_privileged else ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    shipments = list(visible.order_by("-created_at")[:5])
    for s in shipments: s.status_label = STATUS_LABELS.get(s.status, s.status)
    total_val = ContainerItem.objects.filter(shipment__in=visible).aggregate(total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2))))["total"] or 0
    return render(request, "ui/dashboard.html", {"user": user, "shipments": shipments, "total_shipments": visible.count(), "in_transit": visible.filter(status="IN_TRANSIT").count(), "delivered": visible.filter(status="DELIVERED").count(), "total_value": total_val})


@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
    is_privileged = user.role in ("BOSS", "HQ_ADMIN") or getattr(user, "site", "") == "BE"

    shipments = ContainerShipment.objects.all() if is_privileged else ContainerShipment.objects.filter(
        Q(destination_site=user.site) | Q(destination_site__isnull=True)
    )
    shipment = get_object_or_404(shipments, pk=shipment_id)

    # Chat
    if request.method == "POST" and request.POST.get("form_name") == "chat":
        body = (request.POST.get("body") or "").strip()
        if body:
            ChatMessage.objects.create(
                shipment=shipment,
                author=user,
                site=user.site or "BE",
                body=body
            )
        return redirect(f"/shipments/{shipment_id}/#chat")

    # Items
    items = shipment.items.select_related("product").all()
    for item in items:
        item.line_total = item.qty * item.unit_price

    # Documents
    docs = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    for d in docs:
        d.can_share = True

    # Lien partagé (si on revient du partage)
    token = request.GET.get("shared")
    share_url = request.build_absolute_uri(f"/documents/share/{token}/") if token else None

    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")

    return render(request, "ui/shipment_info.html", {
        "shipment": shipment,
        "items": items,
        "documents": docs,
        "share_url": share_url,
        "chat_messages": chat_messages,
    })

@login_required
def shipments_list(request):
    user = request.user
    is_privileged = user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE"
    shipments = ContainerShipment.objects.all() if is_privileged else ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    page_obj = Paginator(shipments.order_by("-created_at"), 20).get_page(request.GET.get("page"))
    for s in page_obj: s.status_label = STATUS_LABELS.get(s.status, s.status)
    return render(request, "ui/shipments_list.html", {"shipments": page_obj, "page_obj": page_obj})

@login_required
def shipment_documents(request, shipment_id: int):
    user = request.user
    is_privileged = user.role in ("BOSS", "HQ_ADMIN") or getattr(user, 'site', '') == "BE"
    shipments = ContainerShipment.objects.all() if is_privileged else ContainerShipment.objects.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
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
                existing = Document.objects.filter(linked_shipment=shipment, doc_type=d_type)
                v = (existing.order_by("-version").first().version + 1) if existing.exists() else 1
                existing.update(is_current=False)
                Document.objects.create(linked_shipment=shipment, doc_type=d_type, file=f, uploaded_by=user, version=v, is_current=True)
                messages.success(request, "Document ajouté")
            return redirect(f"/shipments/{shipment_id}/documents/")
            
    docs = list(Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at"))
    for d in docs: d.can_share = True
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

@login_required
def reports_view(request):
    if request.user.role not in ("BOSS", "HQ_ADMIN"): return redirect("/dashboard/")
    return render(request, "ui/reports.html", {"today": timezone.localdate()})