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
    
    # MODIFICATION : On ajoute "ou si le site est BE"
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
    shipments = ContainerShipment.objects.all()
    
    # MODIFICATION : On ajoute "ou si le site est BE"
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    
    shipment = get_object_or_404(shipments, pk=shipment_id)
    shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)
    
    if request.method == "POST":
        action = request.POST.get("action")
        form_name = request.POST.get("form_name")

        if form_name == "chat":
            body = (request.POST.get("body") or "").strip()
            if body:
                ChatMessage.objects.create(
                    shipment=shipment,
                    author=user,
                    site=user.site or "BE",
                    body=body,
                )
                return redirect(f"/shipments/{shipment_id}/#chat")

        elif action == "upload":
            title = (request.POST.get("title") or "").strip()
            uploaded_file = request.FILES.get("file")
            if title and uploaded_file:
                Document.objects.create(
                    linked_shipment=shipment,
                    title=title,
                    doc_type="AUTRE",
                    file=uploaded_file,
                    uploaded_by=user,
                )
                messages.success(request, "Document ajouté.")
            return redirect(f"/shipments/{shipment_id}/")

    items = shipment.items.select_related("product").all()
    for item in items:
        item.line_total = item.qty * item.unit_price

    documents = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")

    context = {
        "shipment": shipment,
        "items": items,
        "documents": documents,
        "chat_messages": chat_messages,
    }
    return render(request, "ui/shipment_info.html", context)

@login_required
def shipments_list(request):
    user = request.user
    shipments = ContainerShipment.objects.all()
    
    # MODIFICATION : On ajoute "ou si le site est BE"
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))

    status = request.GET.get("status", "").strip()
    site = request.GET.get("site", "").strip()
    date_value = request.GET.get("date", "").strip()

    if status:
        shipments = shipments.filter(status=status)
    if site:
        shipments = shipments.filter(destination_site=site)
    if date_value:
        parsed_date = parse_date(date_value)
        if parsed_date:
            shipments = shipments.filter(Q(etd=parsed_date) | Q(created_at__date=parsed_date))

    shipments = shipments.order_by("-created_at")
    paginator = Paginator(shipments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    for shipment in page_obj:
        shipment.status_label = STATUS_LABELS.get(shipment.status, shipment.status)

    context = {
        "shipments": page_obj,
        "page_obj": page_obj,
        "status": status,
        "site": site,
        "date": date_value,
    }
    return render(request, "ui/shipments_list.html", context)

@login_required
def shipment_documents(request, shipment_id: int):
    user = request.user
    shipments = ContainerShipment.objects.all()
    if user.role not in ("BOSS", "HQ_ADMIN") and getattr(user, 'site', '') != "BE":
        shipments = shipments.filter(Q(destination_site=user.site) | Q(destination_site__isnull=True))
    shipment = get_object_or_404(shipments, pk=shipment_id)

    if request.method == "POST":
        if request.POST.get("action") == "share":
            doc_id = request.POST.get("document_id")
            document = Document.objects.filter(linked_shipment=shipment, pk=doc_id).first()
            can_share = user.role in ("BOSS", "HQ_ADMIN") or (document and document.uploaded_by_id == user.id)
            if not document or not can_share:
                messages.error(request, "Accès refusé.")
            else:
                share = DocumentShare.objects.create(
                    document=document,
                    expire_at=timezone.now() + timedelta(days=7),
                    created_by=user,
                )
                AuditEvent.objects.create(
                    actor=user,
                    action="UPDATE",
                    entity_type="Document",
                    entity_id=str(document.pk),
                    site=shipment.destination_site or "",
                    summary="Document partagé",
                )
                return redirect(f"/shipments/{shipment_id}/documents/?shared={share.token}")
        else:
            doc_type = request.POST.get("doc_type")
            uploaded_file = request.FILES.get("file")
            if not doc_type or not uploaded_file:
                messages.error(request, "Veuillez fournir un type et un fichier.")
            else:
                existing_docs = Document.objects.filter(linked_shipment=shipment, doc_type=doc_type)
                next_version = (existing_docs.order_by("-version").first().version + 1) if existing_docs.exists() else 1
                existing_docs.update(is_current=False)
                Document.objects.create(
                    linked_shipment=shipment,
                    doc_type=doc_type,
                    file=uploaded_file,
                    uploaded_by=user,
                    version=next_version,
                    is_current=True,
                )
                messages.success(request, "Nouveau document ajouté")
                return redirect(f"/shipments/{shipment_id}/documents/")

    documents = list(Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at"))
    for doc in documents:
        doc.can_share = user.role in ("BOSS", "HQ_ADMIN") or doc.uploaded_by_id == user.id
    shared_token = request.GET.get("shared")
    share_url = None
    if shared_token:
        share_url = request.build_absolute_uri(f"/documents/share/{shared_token}/")
    context = {"shipment": shipment, "documents": documents, "share_url": share_url}
    return render(request, "ui/shipment_documents.html", context)

def document_share_view(request, token: str):
    share = DocumentShare.objects.select_related("document", "document__linked_shipment").filter(token=token).first()
    if not share:
        return render(request, "ui/document_share_invalid.html", {"message": "Lien invalide."})
    if share.expire_at < timezone.now():
        return render(request, "ui/document_share_invalid.html", {"message": "Lien expiré."})
    document = share.document
    shipment = document.linked_shipment
    AuditEvent.objects.create(
        actor=share.created_by if share.created_by_id else (request.user if request.user.is_authenticated else None),
        action="UPDATE",
        entity_type="Document",
        entity_id=str(document.pk),
        site=(shipment.destination_site if shipment and shipment.destination_site else "BE"),
        summary=f"Accessed shared document {document.pk}",
    )
    return FileResponse(document.file.open("rb"))

def logout_view(request):
    auth_logout(request)
    return redirect("/login/")

class RoleLoginView(LoginView):
    template_name = "ui/login.html"
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        display_name = getattr(user, 'full_name', None) or user.get_full_name() or user.username
        messages.success(self.request, f"Bienvenue {display_name}")
        return response
    def get_success_url(self):
        return reverse_lazy("dashboard")

@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_avatar":
            avatar = request.FILES.get("avatar")
            if avatar:
                user.avatar = avatar
                user.save(update_fields=["avatar"])
                messages.success(request, "Photo de profil mise à jour.")
            return redirect("/profile/")
        if action == "change_password":
            old_p = request.POST.get("old_password") or ""
            new_p = request.POST.get("new_password") or ""
            conf_p = request.POST.get("confirm_password") or ""
            if user.check_password(old_p) and new_p == conf_p:
                user.set_password(new_p)
                user.save(update_fields=["password"])
                update_session_auth_hash(request, user)
                messages.success(request, "Mot de passe mis à jour.")
            else:
                messages.error(request, "Erreur dans les mots de passe.")
            return redirect("/profile/")
    return render(request, "ui/profile.html", {"user": user})

@login_required
def reports_view(request):
    user = request.user
    if user.role not in ("BOSS", "HQ_ADMIN"):
        messages.error(request, "Accès refusé")
        return redirect("/dashboard/")
    today = timezone.localdate()
    period = request.GET.get("period", "week")
    start_date = today - timedelta(days=29) if period == "month" else today - timedelta(days=6)
    period_label = "Mois" if period == "month" else "Semaine"

    period_shipments = ContainerShipment.objects.filter(created_at__date__gte=start_date, created_at__date__lte=today)
    period_total = period_shipments.count()
    period_value = (
        ContainerItem.objects.filter(shipment__in=period_shipments).aggregate(
            total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2)))
        )["total"] or 0
    )

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="rapport_{period}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Periode", "Total", "Valeur"])
        writer.writerow([period_label, period_total, f"{period_value:.2f}"])
        return response

    context = {
        "today": today,
        "period": period,
        "period_label": period_label,
        "period_total": period_total,
        "period_value": period_value,
        "start_date": start_date,
    }
    return render(request, "ui/reports.html", context)