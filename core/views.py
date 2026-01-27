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

# Modeles de l'application
from audit.models import AuditEvent
from chat.models import ChatMessage
from documents.models import Document, DocumentShare, DocumentSiteShare
from logistics.models import ContainerShipment, ContainerItem

STATUS_LABELS = {
    "CREATED": "Cree",
    "IN_TRANSIT": "En transit",
    "ARRIVED": "Arrive",
    "CLEARED": "Dedouane",
    "DELIVERED": "Livre",
}

def get_visible_shipments(user):
    """
    LOGIQUE CENTRALE : 
    - Le BOSS et la BELGIQUE (BE) voient TOUS les conteneurs.
    - Les autres sites ne voient que leur destination.
    """
    queryset = ContainerShipment.objects.all()
    # Si l'utilisateur n'est pas BOSS/ADMIN et n'est pas du site BE (Belgique)
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        queryset = queryset.filter(
            Q(destination_site=user.site) | Q(destination_site__isnull=True) | Q(destination_site="")
        )
    return queryset

@login_required
def dashboard(request):
    user = request.user
    visible_shipments = get_visible_shipments(user)
    
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
        "user": user,
        "shipments": shipments,
        "total_shipments": total_shipments,
        "in_transit": in_transit,
        "delivered": delivered,
        "total_value": total_value,
    }
    return render(request, "ui/dashboard.html", context)

@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
    visible_shipments = get_visible_shipments(user)
    shipment = get_object_or_404(visible_shipments, pk=shipment_id)
    
    shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)
    
    if request.method == "POST":
        action = request.POST.get("action")
        form_name = request.POST.get("form_name")
        if form_name == "chat":
            body = (request.POST.get("body") or "").strip()
            if body:
                ChatMessage.objects.create(shipment=shipment, author=user, site=user.site or "BE", body=body)
                return redirect(f"/shipments/{shipment_id}/#chat")
        elif action == "upload":
            title = (request.POST.get("title") or "").strip()
            uploaded_file = request.FILES.get("file")
            if title and uploaded_file:
                Document.objects.create(linked_shipment=shipment, title=title, doc_type="AUTRE", file=uploaded_file, uploaded_by=user)
                messages.success(request, "Document ajoute.")
            return redirect(f"/shipments/{shipment_id}/")

    items = shipment.items.select_related("product").all()
    for item in items:
        item.line_total = item.qty * item.unit_price

    documents = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")

    context = {"shipment": shipment, "items": items, "documents": documents, "chat_messages": chat_messages}
    return render(request, "ui/shipment_info.html", context)

@login_required
def shipments_list(request):
    user = request.user
    shipments = get_visible_shipments(user)

    status = request.GET.get("status", "").strip()
    site = request.GET.get("site", "").strip()
    date_value = request.GET.get("date", "").strip()

    if status: shipments = shipments.filter(status=status)
    if site: shipments = shipments.filter(destination_site=site)
    if date_value:
        parsed_date = parse_date(date_value)
        if parsed_date:
            shipments = shipments.filter(Q(etd=parsed_date) | Q(created_at__date=parsed_date))

    shipments = shipments.order_by("-created_at")
    paginator = Paginator(shipments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    for shipment in page_obj:
        shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)

    context = {"shipments": page_obj, "page_obj": page_obj, "status": status, "site": site, "date": date_value}
    return render(request, "ui/shipments_list.html", context)

@login_required
def profile_view(request):
    return render(request, "ui/profile.html", {"user": request.user})

def logout_view(request):
    auth_logout(request)
    return redirect("/login/")

class RoleLoginView(LoginView):
    template_name = "ui/login.html"
    def get_success_url(self):
        return reverse_lazy("dashboard")