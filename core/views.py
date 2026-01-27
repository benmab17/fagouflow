import csv
from datetime import timedelta

# Django Core & Auth
from django.contrib import messages
from django.contrib.auth import logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date

# Modèles de l'application
from audit.models import AuditEvent
from chat.models import ChatMessage
from documents.models import Document, DocumentShare, DocumentSiteShare
from logistics.models import ContainerShipment, ContainerItem

STATUS_LABELS = {
    "CREATED": "Créé",
    "IN_TRANSIT": "En transit",
    "ARRIVED": "Arrivé",
    "CLEARED": "Dédouané",
    "DELIVERED": "Livré",
}

@login_required
def dashboard(request):
    user = request.user
    visible_shipments = ContainerShipment.objects.all()
    # Règle Germaine : Si pas BOSS/ADMIN ET pas site BE, on filtre
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        visible_shipments = visible_shipments.filter(
            Q(destination_site=user.site) | Q(destination_site__isnull=True)
        )
    shipments = list(visible_shipments.order_by("-created_at")[:5])
    for shipment in shipments:
        shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)
    
    total_shipments = visible_shipments.count()
    in_transit = visible_shipments.filter(status="IN_TRANSIT").count()
    delivered = visible_shipments.filter(status="DELIVERED").count()
    
    total_value = (
        ContainerItem.objects.filter(shipment__in=visible_shipments).aggregate(
            total=Sum(
                ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2))
            )
        )["total"] or 0
    )
    context = {
        "user": user, "shipments": shipments, "total_shipments": total_shipments,
        "in_transit": in_transit, "delivered": delivered, "total_value": total_value,
    }
    return render(request, "ui/dashboard.html", context)

@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
    shipments = ContainerShipment.objects.all()
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    
    shipment = get_object_or_404(shipments, pk=shipment_id)
    shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)
    
    if request.method == "POST":
        form_name = request.POST.get("form_name")
        if form_name == "chat":
            body = (request.POST.get("body") or "").strip()
            if body:
                ChatMessage.objects.create(shipment=shipment, author=user, site=user.site or "BE", body=body)
                return redirect(f"/shipments/{shipment_id}/#chat")
        elif request.POST.get("action") == "upload":
            title, uploaded_file = request.POST.get("title", "").strip(), request.FILES.get("file")
            if title and uploaded_file:
                Document.objects.create(linked_shipment=shipment, title=title, doc_type="AUTRE", file=uploaded_file, uploaded_by=user)
                messages.success(request, "Document ajouté.")
            return redirect(f"/shipments/{shipment_id}/")

    items = shipment.items.select_related("product").all()
    for item in items: item.line_total = item.qty * item.unit_price
    documents = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")
    return render(request, "ui/shipment_info.html", {"shipment": shipment, "items": items, "documents": documents, "chat_messages": chat_messages})

@login_required
def shipments_list(request):
    user = request.user
    shipments = ContainerShipment.objects.all()
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))

    status, site, date_val = request.GET.get("status", ""), request.GET.get("site", ""), request.GET.get("date", "")
    if status: shipments = shipments.filter(status=status)
    if site: shipments = shipments.filter(destination_site=site)
    if date_val:
        p_date = parse_date(date_val)
        if p_date: shipments = shipments.filter(Q(etd=p_date) | Q(created_at__date=p_date))

    page_obj = Paginator(shipments.order_by("-created_at"), 20).get_page(request.GET.get("page"))
    for s in page_obj: s.status_label = STATUS_LABELS.get(s.status, s.status)
    return render(request, "ui/shipments_list.html", {"shipments": page_obj, "page_obj": page_obj, "status": status, "site": site, "date": date_val})

@login_required
def shipment_documents(request, shipment_id: int):
    user = request.user
    shipments = ContainerShipment.objects.all()
    # Règle Germaine : BOSS ou BE voient tout
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    
    shipment = get_object_or_404(shipments, pk=shipment_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "share":
            doc_id = request.POST.get("document_id")
            doc = Document.objects.filter(linked_shipment=shipment, pk=doc_id).first()
            # On autorise le partage si BOSS, proprio du doc, ou site BE
            if doc and (user.role in ("BOSS", "HQ_ADMIN") or doc.uploaded_by_id == user.id or getattr(user, 'site', '') == "BE"):
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

    # --- CRUCIAL : On prépare les documents pour le HTML ---
    docs = list(Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at"))
    for d in docs:
        # On définit explicitement can_share pour que ton template {% if doc.can_share %} fonctionne
        d.can_share = (user.role in ("BOSS", "HQ_ADMIN") or d.uploaded_by_id == user.id or getattr(user, 'site', '') == "BE")

    token = request.GET.get("shared")
    url = request.build_absolute_uri(f"/documents/share/{token}/") if token else None
    
    return render(request, "ui/shipment_documents.html", {
        "shipment": shipment, 
        "documents": docs, 
        "share_url": url
    })