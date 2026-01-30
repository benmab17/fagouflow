import csv
import os
from functools import wraps
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import FileResponse, HttpResponse, Http404, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date

# Import de tes modèles
from chat.models import ChatMessage, ClientChatMessage
from core.alerts import build_alerts
from core.models import ShipmentUpdate
from documents.models import Document, DocumentShare
from logistics.models import ContainerShipment, ContainerItem, StatusHistory

# Fly.io health check (lightweight, no auth, no DB)
def healthz(request):
    if request.method != "GET":
        return HttpResponse("method not allowed", content_type="text/plain", status=405)
    return HttpResponse("ok", content_type="text/plain", status=200)

 # PREVIEW ONLY – TO DELETE: mock data for client portal UI
def preview_client_dashboard(request):
    today = timezone.now().date()
    containers = [
        {
            "id": 1,
            "reference": "CMAU1234567",
            "container_no": "CMAU1234567",
            "origin": "CM",
            "origin_country": "CM",
            "destination": "PN",
            "destination_site": "PN",
            "status": "IN_TRANSIT",
            "eta": today + timedelta(days=3),
            "priority": "PRIORITÉ HAUTE",
            "updated_at": timezone.now(),
            "created_at": timezone.now() - timedelta(days=5),
        },
        {
            "id": 2,
            "reference": "MSCU7654321",
            "container_no": "MSCU7654321",
            "origin": "CN",
            "origin_country": "CN",
            "destination": "DLA",
            "destination_site": "DLA",
            "status": "CREATED",
            "eta": today + timedelta(days=10),
            "priority": "PRIORITÉ",
            "updated_at": timezone.now() - timedelta(hours=6),
            "created_at": timezone.now() - timedelta(days=2),
        },
        {
            "id": 3,
            "reference": "TGHU9988776",
            "container_no": "TGHU9988776",
            "origin": "US",
            "origin_country": "US",
            "destination": "KIN",
            "destination_site": "KIN",
            "status": "DELIVERED",
            "eta": today - timedelta(days=1),
            "priority": None,
            "updated_at": timezone.now() - timedelta(days=1, hours=3),
            "created_at": timezone.now() - timedelta(days=15),
        },
        {
            "id": 4,
            "reference": "OOLU1122334",
            "container_no": "OOLU1122334",
            "origin": "DE",
            "origin_country": "DE",
            "destination": "PN",
            "destination_site": "PN",
            "status": "IN_TRANSIT",
            "eta": today - timedelta(days=2),
            "priority": "PRIORITÉ",
            "updated_at": timezone.now() - timedelta(hours=2),
            "created_at": timezone.now() - timedelta(days=9),
        },
        {
            "id": 5,
            "reference": "MSCU4455667",
            "container_no": "MSCU4455667",
            "origin": "ES",
            "origin_country": "ES",
            "destination": "DLA",
            "destination_site": "DLA",
            "status": "CREATED",
            "eta": today + timedelta(days=12),
            "priority": None,
            "updated_at": timezone.now() - timedelta(days=1),
            "created_at": timezone.now() - timedelta(days=1, hours=5),
        },
        {
            "id": 6,
            "reference": "CMAU3344556",
            "container_no": "CMAU3344556",
            "origin": "FR",
            "origin_country": "FR",
            "destination": "KIN",
            "destination_site": "KIN",
            "status": "DELIVERED",
            "eta": today - timedelta(days=6),
            "priority": None,
            "updated_at": timezone.now() - timedelta(days=5),
            "created_at": timezone.now() - timedelta(days=20),
        },
    ]
    total_count = len(containers)
    in_transit_count = len([c for c in containers if c["status"] == "IN_TRANSIT"])
    delivered_count = len([c for c in containers if c["status"] == "DELIVERED"])
    late_count = len([c for c in containers if c["status"] == "IN_TRANSIT" and c["eta"] < today])
    return render(request, "client/dashboard.html", {
        "containers": containers,
        "total_count": total_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "late_count": late_count,
    })

STATUS_LABELS = {
    "CREATED": "Créé", 
    "IN_TRANSIT": "En transit", 
    "ARRIVED": "Arrivé", 
    "CLEARED": "Dédouané", 
    "DELIVERED": "Livré"
}

def get_user_site(user):
    """Utilitaire pour éviter les erreurs si l'user n'a pas de site"""
    return getattr(user, 'site', None)

def get_visible_shipments(user):
    """Filtre les expéditions selon le rôle et le site"""
    role = getattr(user, 'role', 'USER')
    site = get_user_site(user)
    
    is_privileged = role in ("BOSS", "HQ_ADMIN") or site == "BE"
    
    if is_privileged:
        return ContainerShipment.objects.all()
    return ContainerShipment.objects.filter(Q(destination_site=site) | Q(destination_site__isnull=True))


def get_client_key(user):
    full_name = (getattr(user, "full_name", "") or "").strip()
    if full_name:
        return full_name
    email = (getattr(user, "email", "") or "").strip()
    if email and "@" in email:
        return email.split("@")[0]
    return email


def get_client_shipments(user):
    client = getattr(user, "client", None)
    if not client:
        return ContainerShipment.objects.none()
    return ContainerShipment.objects.filter(client=client)


def get_avatar_url(author):
    if not author:
        return None
    avatar = getattr(author, "avatar", None)
    if avatar:
        try:
            url = avatar.url
            if url:
                return url
        except Exception:
            pass
    local_avatar = getattr(author, "local_avatar", None)
    if local_avatar:
        try:
            url = local_avatar.url
            if url:
                return url
        except Exception:
            pass
    url = getattr(author, "avatar_url", None)
    if url:
        return url
    return None


def build_chat_messages_ui(messages, current_user):
    chat_messages_ui = []
    prev_author_id = None
    prev_date = None
    for m in messages:
        author = getattr(m, "author", None)
        full = ""
        if author:
            try:
                full = (author.get_full_name() or "").strip()
            except Exception:
                full = ""
        if full:
            author_name = full
        else:
            first = (getattr(author, "first_name", "") or "").strip() if author else ""
            last = (getattr(author, "last_name", "") or "").strip() if author else ""
            if first or last:
                author_name = f"{first} {last}".strip()
            else:
                email = (getattr(author, "email", "") or "").strip() if author else ""
                author_name = email.split("@")[0] if email and "@" in email else (email or "Utilisateur")

        initials_source = author_name or "U"
        initials = initials_source[:2].upper()
        avatar_url = get_avatar_url(author)

        msg_date = m.created_at.date() if m.created_at else None
        show_date_separator = bool(msg_date and msg_date != prev_date)
        show_avatar = bool(author and author.pk != prev_author_id)
        is_client = getattr(author, "role", "") == "CLIENT"

        chat_messages_ui.append({
            "author_name": author_name,
            "initials": initials,
            "avatar_url": avatar_url,
            "body": m.body,
            "created_at": m.created_at,
            "date_label": m.created_at.strftime("%d/%m/%Y") if m.created_at else "",
            "show_date_separator": show_date_separator,
            "show_avatar": show_avatar,
            "is_client": is_client,
            "is_me": author == current_user,
        })

        prev_author_id = author.pk if author else None
        prev_date = msg_date
    return chat_messages_ui


def _is_client(user):
    return getattr(user, "role", "") == "CLIENT"

def _is_linked_client(user):
    try:
        return getattr(user, "client_id", None) is not None
    except Exception:
        return False

def client_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(reverse("client_login"))
        if _is_linked_client(user):
            return view_func(request, *args, **kwargs)
        if user.is_staff:
            return redirect(reverse("dashboard"))
        raise PermissionDenied
    return _wrapped


def _redirect_client_if_needed(user):
    # Sécurité navigation: un client ne doit pas accéder aux vues internes.
    if _is_client(user):
        return redirect("/client/")
    return None


def _redirect_non_client_if_needed(user):
    # Permettre l'accès aux vues /client/ pour tout utilisateur authentifié.
    return None

@login_required
def dashboard(request):
    user = request.user
    redirect_response = _redirect_client_if_needed(user)
    if redirect_response:
        return redirect_response
    visible = get_visible_shipments(user)
    
    shipments = list(visible.order_by("-created_at")[:5])
    for s in shipments: 
        s.status_label = STATUS_LABELS.get(s.status, s.status)
    
    # Calcul de la valeur totale avec gestion des cas vides
    total_val = ContainerItem.objects.filter(shipment__in=visible).aggregate(
        total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2)))
    )["total"] or 0

    q = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    dest_filter = (request.GET.get("destination") or "").strip()

    track_qs = visible.order_by("-created_at")
    if q:
        track_qs = track_qs.filter(
            Q(container_no__icontains=q) |
            Q(bl_no__icontains=q) |
            Q(client_name__icontains=q)
        )
    if status_filter and status_filter != "ALL":
        track_qs = track_qs.filter(status=status_filter)
    if dest_filter and dest_filter != "ALL":
        track_qs = track_qs.filter(destination_site=dest_filter)

    track_shipments = list(track_qs[:20])
    for s in track_shipments:
        s.status_label = STATUS_LABELS.get(s.status, s.status)

    status_options = [choice[0] for choice in getattr(ContainerShipment, "STATUS_CHOICES", [])]
    destination_options = list(
        visible.exclude(destination_site__isnull=True)
        .exclude(destination_site="")
        .values_list("destination_site", flat=True)
        .distinct()
    )
    
    alerts = build_alerts(visible)

    activities = []
    try:
        doc_qs = Document.objects.filter(linked_shipment__in=visible).select_related("uploaded_by", "linked_shipment").order_by("-uploaded_at")[:15]
        for d in doc_qs:
            activities.append({
                "timestamp": d.uploaded_at,
                "user": d.uploaded_by,
                "action": f"a ajouté un document {d.doc_type} (v{d.version})",
                "shipment_id": d.linked_shipment_id,
                "container_code": getattr(d.linked_shipment, "container_no", ""),
            })
    except Exception:
        pass

    try:
        chat_qs = ChatMessage.objects.filter(shipment__in=visible).select_related("author", "shipment").order_by("-created_at")[:15]
        for m in chat_qs:
            activities.append({
                "timestamp": m.created_at,
                "user": m.author,
                "action": "a envoyé un message",
                "shipment_id": m.shipment_id,
                "container_code": getattr(m.shipment, "container_no", ""),
            })
    except Exception:
        pass

    try:
        upd_qs = ShipmentUpdate.objects.filter(shipment__in=visible).select_related("created_by", "shipment").order_by("-created_at")[:15]
        for u in upd_qs:
            activities.append({
                "timestamp": u.created_at,
                "user": u.created_by,
                "action": f"statut mis à jour: {u.status}",
                "shipment_id": u.shipment_id,
                "container_code": getattr(u.shipment, "container_no", ""),
            })
    except Exception:
        pass

    activities = sorted([a for a in activities if a.get("timestamp")], key=lambda a: a["timestamp"], reverse=True)[:15]

    return render(request, "ui/dashboard.html", {
        "user": user, 
        "shipments": shipments, 
        "total_shipments": visible.count(), 
        "in_transit": visible.filter(status="IN_TRANSIT").count(), 
        "delivered": visible.filter(status="DELIVERED").count(), 
        "total_value": total_val,
        "alerts": alerts,
        "alerts_count": len(alerts),
        "activities": activities,
        "track_shipments": track_shipments,
        "q": q,
        "status_filter": status_filter or "ALL",
        "destination_filter": dest_filter or "ALL",
        "status_options": status_options,
        "destination_options": destination_options,
    })


@login_required
def dashboard_export(request):
    visible = get_visible_shipments(request.user).order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="shipments.csv"'
    writer = csv.writer(response)
    writer.writerow(["container_no", "bl_no", "status", "destination_site", "client_name", "created_at"])
    for s in visible:
        writer.writerow([
            s.container_no,
            s.bl_no,
            s.status,
            s.destination_site or "",
            s.client_name or "",
            s.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


@login_required
def direction_view(request):
    user = request.user
    role = getattr(user, "role", "")
    # Clients redirigés systématiquement.
    redirect_response = _redirect_client_if_needed(user)
    if redirect_response:
        return redirect_response
    # Accès direction uniquement BOSS/HQ_ADMIN/staff/superuser.
    if not (role in ("BOSS", "HQ_ADMIN") or user.is_staff or user.is_superuser):
        messages.error(request, "Acces reserve a la direction.")
        return redirect("/dashboard/")

    visible = get_visible_shipments(user)
    now = timezone.now()
    transit_days = int(getattr(settings, "ALERTS_TRANSIT_DAYS", 7))
    required_docs = list(getattr(settings, "ALERTS_REQUIRED_DOC_TYPES", ["BL", "INVOICE"]))

    total_count = visible.count()
    in_transit_qs = visible.filter(status="IN_TRANSIT")
    delivered_qs = visible.filter(status="DELIVERED")
    active_qs = visible.exclude(status="DELIVERED")

    total_value = None
    try:
        total_value = ContainerItem.objects.filter(shipment__in=visible).aggregate(
            total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2)))
        )["total"]
    except Exception:
        total_value = None

    blocked_count = 0
    try:
        blocked_count = visible.filter(status__in=["EN_DOUANE", "BLOCKED"]).count()
    except Exception:
        blocked_count = 0

    # Docs missing on active shipments
    missing_docs_count = 0
    doc_ids = set()
    if required_docs:
        try:
            doc_ids = set(Document.objects.filter(linked_shipment__in=active_qs, doc_type__in=required_docs).values_list("linked_shipment_id", "doc_type"))
            for s in active_qs:
                if any((s.id, d) not in doc_ids for d in required_docs):
                    missing_docs_count += 1
        except Exception:
            missing_docs_count = 0

    # Risk scoring
    risk_items = []
    field_names = {f.name for f in ContainerShipment._meta.get_fields()}
    for s in active_qs.order_by("-created_at")[:200]:
        score = 0
        reasons = []
        if not getattr(s, "destination_site", None):
            score += 2
            reasons.append("Destination manquante")
        if required_docs and doc_ids and any((s.id, d) not in doc_ids for d in required_docs):
            score += 2
            reasons.append("Docs manquants")
        if s.status == "IN_TRANSIT":
            score += 1
            reasons.append("En transit")
        if "eta" in field_names:
            if getattr(s, "eta", None) and s.eta < now.date():
                score += 1
                reasons.append("ETA depassee")
        else:
            if s.created_at.date() < now.date() - timedelta(days=transit_days):
                score += 1
                reasons.append("Ancien")
        if score:
            risk_items.append({
                "shipment": s,
                "score": score,
                "reasons": ", ".join(reasons),
            })
    risk_items = sorted(risk_items, key=lambda x: x["score"], reverse=True)[:5]

    risks_count = len(risk_items)

    # Quality
    status_breakdown = list(visible.values("status").annotate(count=Count("id")).order_by("-count"))
    docs_quality = None
    if required_docs and active_qs.exists():
        try:
            total_active = active_qs.count()
            bl_have = len({sid for sid, dt in doc_ids if dt == "BL"})
            inv_have = len({sid for sid, dt in doc_ids if dt == "INVOICE"})
            docs_quality = {
                "bl_pct": round((bl_have / total_active) * 100, 1) if total_active else None,
                "inv_pct": round((inv_have / total_active) * 100, 1) if total_active else None,
            }
        except Exception:
            docs_quality = None

    # Activity week
    week_start = now - timedelta(days=7)
    docs_week = None
    chats_week = None
    try:
        docs_week = Document.objects.filter(uploaded_at__gte=week_start, linked_shipment__in=visible).count()
    except Exception:
        docs_week = None
    try:
        chats_week = ChatMessage.objects.filter(created_at__gte=week_start, shipment__in=visible).count()
    except Exception:
        chats_week = None

    context = {
        "total_count": total_count,
        "in_transit_count": in_transit_qs.count(),
        "delivered_count": delivered_qs.count(),
        "blocked_count": blocked_count,
        "missing_docs_count": missing_docs_count,
        "total_value": total_value,
        "risks_count": risks_count,
        "risk_items": risk_items,
        "status_breakdown": status_breakdown,
        "docs_quality": docs_quality,
        "docs_week": docs_week,
        "chats_week": chats_week,
    }
    return render(request, "ui/direction.html", context)


@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
    if getattr(user, "role", "") == "CLIENT":
        return redirect(f"/client/containers/{shipment_id}/")
    shipments = get_visible_shipments(user)
    shipment = get_object_or_404(shipments, pk=shipment_id)

    if request.method == "POST":
        form_name = request.POST.get("form_name")
        action = request.POST.get("action")

        # 1. LOGIQUE DU CHAT (Ton code actuel)
        if form_name == "chat":
            body = (request.POST.get("body") or "").strip()
            if body:
                ChatMessage.objects.create(
                    shipment=shipment,
                    author=user,
                    site=get_user_site(user) or "BE",
                    body=body
                )
            return redirect(f"/shipments/{shipment_id}/#chat")

        # 2. LOGIQUE DES DOCUMENTS (Nouveau)
        # On vérifie soit le form_name, soit l'action 'upload' que j'ai mis dans le HTML
        if action == "upload":
            file = request.FILES.get("file")
            doc_type = request.POST.get("doc_type")
            if file and doc_type:
                # On crée le document en base de données
                Document.objects.create(
                    linked_shipment=shipment,
                    doc_type=doc_type,
                    file=file,
                    uploaded_by=user
                )
                
                # OPTIONNEL : Créer une ligne d'historique automatique pour l'ajout
                ShipmentUpdate.objects.create(
                    shipment=shipment,
                    status=shipment.status,
                    notes=f"Document '{doc_type}' ajouté par {user.username}"
                )
            return redirect(f"/shipments/{shipment_id}/")

    # --- LE RESTE RESTE PAREIL ---
    items = shipment.items.select_related("product").all()
    for item in items:
        item.line_total = (item.qty or 0) * (item.unit_price or 0)

    docs = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    
    # Historique (Vérifie que le nom du modèle est bien ShipmentUpdate)
    updates = ShipmentUpdate.objects.filter(shipment=shipment).order_by("-created_at")

    def get_avatar_url(author, req=None):
        if not author:
            return None
        # A) primary avatar field
        avatar = getattr(author, "avatar", None)
        if avatar:
            try:
                url = avatar.url
                if url:
                    return url
            except Exception:
                pass
        # B) local avatar field
        local_avatar = getattr(author, "local_avatar", None)
        if local_avatar:
            try:
                url = local_avatar.url
                if url:
                    return url
            except Exception:
                pass
        # C) precomputed property
        url = getattr(author, "avatar_url", None)
        if url:
            return url
        return None

    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")
    chat_messages_ui = []
    prev_author_id = None
    prev_date = None
    for m in chat_messages:
        author = getattr(m, "author", None)
        full = ""
        if author:
            try:
                full = (author.get_full_name() or "").strip()
            except Exception:
                full = ""
        if full:
            author_name = full
        else:
            first = (getattr(author, "first_name", "") or "").strip() if author else ""
            last = (getattr(author, "last_name", "") or "").strip() if author else ""
            if first or last:
                author_name = f"{first} {last}".strip()
            else:
                email = (getattr(author, "email", "") or "").strip() if author else ""
                author_name = email.split("@")[0] if email and "@" in email else (email or "Utilisateur")

        initials_source = author_name or "U"
        initials = initials_source[:2].upper()

        avatar_url = get_avatar_url(author, request)

        msg_date = m.created_at.date() if m.created_at else None
        show_date_separator = bool(msg_date and msg_date != prev_date)
        show_avatar = bool(author and author.pk != prev_author_id)

        chat_messages_ui.append({
            "author_name": author_name,
            "initials": initials,
            "avatar_url": avatar_url,
            "body": m.body,
            "created_at": m.created_at,
            "date_label": m.created_at.strftime("%d/%m/%Y") if m.created_at else "",
            "show_date_separator": show_date_separator,
            "show_avatar": show_avatar,
            "is_me": author == user,
        })

        prev_author_id = author.pk if author else None
        prev_date = msg_date

    return render(request, "ui/shipment_info.html", {
        "shipment": shipment,
        "items": items,
        "documents": docs,
        "chat_messages": chat_messages_ui,
        "updates": updates, # On passe l'historique au template
        "focus_chat": request.GET.get("focus") == "chat",
    })



@login_required
def shipments_list(request):
    visible = get_visible_shipments(request.user)
    paginator = Paginator(visible.order_by("-created_at"), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    for s in page_obj: 
        s.status_label = STATUS_LABELS.get(s.status, s.status)
        
    return render(request, "ui/shipments_list.html", {"shipments": page_obj, "page_obj": page_obj})


@login_required
@client_required
def client_portal(request):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {
            "client_missing": True,
            "is_client_portal": True,
        })

    q = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    dest_filter = (request.GET.get("destination") or "").strip()

    shipments = get_client_shipments(user).order_by("-created_at")
    if q:
        shipments = shipments.filter(
            Q(container_no__icontains=q) |
            Q(bl_no__icontains=q) |
            Q(client_name__icontains=q)
        )
    if status_filter and status_filter != "ALL":
        shipments = shipments.filter(status=status_filter)
    if dest_filter and dest_filter != "ALL":
        shipments = shipments.filter(destination_site=dest_filter)

    shipments = list(shipments[:50])
    updates = ShipmentUpdate.objects.filter(shipment__in=shipments).order_by("-created_at")
    latest_by_shipment = {}
    for u in updates:
        if u.shipment_id not in latest_by_shipment:
            latest_by_shipment[u.shipment_id] = u.created_at
    doc_counts = {}
    try:
        doc_counts = {
            row["linked_shipment_id"]: row["count"]
            for row in Document.objects.filter(linked_shipment__in=shipments)
            .values("linked_shipment_id")
            .annotate(count=Count("id"))
        }
    except Exception:
        doc_counts = {}
    for s in shipments:
        s.last_update = latest_by_shipment.get(s.id, s.created_at)
        s.docs_count = doc_counts.get(s.id, 0)
    for s in shipments:
        s.status_label = STATUS_LABELS.get(s.status, s.status)

    status_options = [choice[0] for choice in getattr(ContainerShipment, "STATUS_CHOICES", [])]
    destination_options = list(
        get_client_shipments(user)
        .exclude(destination_site__isnull=True)
        .exclude(destination_site="")
        .values_list("destination_site", flat=True)
        .distinct()
    )
    total_count = get_client_shipments(user).count()
    in_transit_count = get_client_shipments(user).filter(status="IN_TRANSIT").count()
    delivered_count = get_client_shipments(user).filter(status="DELIVERED").count()
    return render(request, "ui/client_portal.html", {
        "shipments": shipments,
        "q": q,
        "status_filter": status_filter or "ALL",
        "destination_filter": dest_filter or "ALL",
        "status_options": status_options,
        "destination_options": destination_options,
        "total_count": total_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "is_client_portal": True,
    })


@login_required
@client_required
def dashboard_client(request):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    shipments = get_client_shipments(user)
    today = timezone.now().date()
    total_count = shipments.count()
    in_transit_count = shipments.filter(status="IN_TRANSIT").count()
    delivered_count = shipments.filter(status="DELIVERED").count()
    late_count = shipments.filter(status="IN_TRANSIT", eta__lt=today).count()
    containers = shipments.order_by("-created_at")[:20]

    return render(request, "client/dashboard.html", {
        "total_count": total_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "late_count": late_count,
        "containers": containers,
    })


@login_required
@client_required
def containers_list(request):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    shipments = get_client_shipments(user).order_by("-created_at")
    paginator = Paginator(shipments, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "client/containers_list.html", {"page_obj": page_obj})


@login_required
@client_required
def container_detail(request, id: int):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    container = get_object_or_404(get_client_shipments(user), pk=id)

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if body:
            ClientChatMessage.objects.create(
                shipment=container,
                author=user,
                sender_type="client",
                body=body,
            )
        return redirect(f"/client/containers/{id}/")

    messages_qs = ClientChatMessage.objects.filter(shipment=container).select_related("author").order_by("created_at")
    chat_messages_ui = build_chat_messages_ui(messages_qs, user)
    return render(
        request,
        "client/container_detail.html",
        {"container": container, "chat_messages": chat_messages_ui},
    )


@login_required
@client_required
def client_container_documents(request, id: int):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    container = get_object_or_404(get_client_shipments(user), pk=id)
    docs = Document.objects.filter(linked_shipment=container).order_by("-uploaded_at")
    return render(request, "client/container_documents.html", {"container": container, "documents": docs})


@login_required
@client_required
def client_container_history(request, id: int):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    container = get_object_or_404(get_client_shipments(user), pk=id)
    updates = ShipmentUpdate.objects.filter(shipment=container).order_by("-created_at")
    status_history = StatusHistory.objects.filter(shipment=container).order_by("-changed_at")
    return render(
        request,
        "client/container_history.html",
        {"container": container, "updates": updates, "status_history": status_history},
    )


@login_required
@client_required
def client_container_chat(request, id: int):
    user = request.user
    redirect_response = _redirect_non_client_if_needed(user)
    if redirect_response:
        return redirect_response
    if not getattr(user, "client", None):
        return render(request, "ui/client_portal.html", {"client_missing": True, "is_client_portal": True})

    container = get_object_or_404(get_client_shipments(user), pk=id)
    return redirect(f"/client/containers/{container.id}/")


@login_required
def client_shipment_detail(request, shipment_id: int):
    return redirect(f"/client/containers/{shipment_id}/")


@login_required
def client_shipment_discussion(request, shipment_id: int):
    return redirect(f"/client/containers/{shipment_id}/chat/")



@login_required
def shipment_documents(request, shipment_id: int):
    user = request.user
    shipments = get_visible_shipments(user)
    shipment = get_object_or_404(shipments, pk=shipment_id)
    
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "share":
            doc_id = request.POST.get("document_id")
            doc = Document.objects.filter(linked_shipment=shipment, pk=doc_id).first()
            if doc:
                share = DocumentShare.objects.create(
                    document=doc, 
                    expire_at=timezone.now() + timedelta(days=7), 
                    created_by=user
                )
                return redirect(f"/shipments/{shipment_id}/documents/?shared={share.token}")
        else:
            d_type = request.POST.get("doc_type")
            f = request.FILES.get("file")
            if d_type and f:
                existing = Document.objects.filter(linked_shipment=shipment, doc_type=d_type)
                last_doc = existing.order_by("-version").first()
                v = (last_doc.version + 1) if last_doc else 1
                
                existing.update(is_current=False)
                Document.objects.create(
                    linked_shipment=shipment, 
                    doc_type=d_type, 
                    file=f, 
                    uploaded_by=user, 
                    version=v, 
                    is_current=True
                )
                messages.success(request, "Document ajouté avec succès.")
            return redirect(f"/shipments/{shipment_id}/documents/")
            
    docs = Document.objects.filter(linked_shipment=shipment).order_by("-uploaded_at")
    for d in docs: 
        d.can_share = True
        
    token = request.GET.get("shared")
    url = request.build_absolute_uri(f"/documents/share/{token}/") if token else None
    
    return render(request, "ui/shipment_documents.html", {
        "shipment": shipment, 
        "documents": docs, 
        "share_url": url
    })

def document_share_view(request, token: str):
    share = DocumentShare.objects.filter(token=token).first()
    if not share or share.expire_at < timezone.now():
        return render(request, "ui/document_share_invalid.html", {"message": "Lien invalide ou expiré"}, status=403)
    
    try:
        return FileResponse(share.document.file.open("rb"))
    except (FileNotFoundError, ValueError):
        raise Http404("Le fichier physique est introuvable sur le serveur.")

def logout_view(request):
    auth_logout(request)
    return redirect("/login/")

class RoleLoginView(LoginView):
    template_name = "ui/login.html"
    def get_success_url(self): 
        user = self.request.user
        if user.is_staff:
            return "/dashboard/"
        return "/client/"

class ClientLoginView(LoginView):
    template_name = "ui/login.html"
    def get_success_url(self):
        return "/client/"

@login_required
def profile_view(request):
    user = request.user
    avatar_url = None
    cloud_name = (
        getattr(settings, "CLOUDINARY_CLOUD_NAME", None)
        or os.environ.get("CLOUDINARY_CLOUD_NAME")
        or os.environ.get("CLOUDINARY_URL")
    )
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_avatar":
            file = request.FILES.get("avatar")
            if not file:
                messages.error(request, "Veuillez sélectionner une image.")
                return redirect("/profile/")
            if cloud_name:
                user.avatar = file
                user.save(update_fields=["avatar"])
            else:
                user.local_avatar = file
                user.save(update_fields=["local_avatar"])
            messages.success(request, "Photo de profil mise à jour.")
            return redirect("/profile/")
    try:
        if cloud_name:
            avatar = getattr(user, "avatar", None)
            if avatar:
                avatar_url = avatar.url
        else:
            local_avatar = getattr(user, "local_avatar", None)
            if local_avatar:
                avatar_url = local_avatar.url
    except Exception:
        avatar_url = None
    return render(request, "ui/profile.html", {"user": user, "avatar_url": avatar_url})

@login_required
def reports_view(request):
    role = getattr(request.user, 'role', 'USER')
    if role not in ("BOSS", "HQ_ADMIN"):
        return redirect("/dashboard/")
    return render(request, "ui/reports.html", {"today": timezone.localdate()})
