import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import FileResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date

# Import de tes modèles
from chat.models import ChatMessage
from documents.models import Document, DocumentShare
from logistics.models import ContainerShipment, ContainerItem

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

@login_required
def dashboard(request):
    user = request.user
    visible = get_visible_shipments(user)
    
    shipments = list(visible.order_by("-created_at")[:5])
    for s in shipments: 
        s.status_label = STATUS_LABELS.get(s.status, s.status)
    
    # Calcul de la valeur totale avec gestion des cas vides
    total_val = ContainerItem.objects.filter(shipment__in=visible).aggregate(
        total=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2)))
    )["total"] or 0
    
    return render(request, "ui/dashboard.html", {
        "user": user, 
        "shipments": shipments, 
        "total_shipments": visible.count(), 
        "in_transit": visible.filter(status="IN_TRANSIT").count(), 
        "delivered": visible.filter(status="DELIVERED").count(), 
        "total_value": total_val
    })


@login_required
def shipment_detail(request, shipment_id: int):
    user = request.user
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
    updates = shipment.updates.all().order_by("-created_at")

    chat_messages = ChatMessage.objects.filter(shipment=shipment).select_related("author").order_by("created_at")

    return render(request, "ui/shipment_info.html", {
        "shipment": shipment,
        "items": items,
        "documents": docs,
        "chat_messages": chat_messages,
        "updates": updates, # On passe l'historique au template
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
        return reverse_lazy("dashboard")

@login_required
def profile_view(request):
    return render(request, "ui/profile.html", {"user": request.user})

@login_required
def reports_view(request):
    role = getattr(request.user, 'role', 'USER')
    if role not in ("BOSS", "HQ_ADMIN"):
        return redirect("/dashboard/")
    return render(request, "ui/reports.html", {"today": timezone.localdate()})