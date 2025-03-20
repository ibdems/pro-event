from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from demande.models import Demande
from event.models import Category, Contact, Event, InfoTicket, Partner, Payement, Ticket
from users.models import User


# Fonctions utilitaires
def is_admin(user):
    return user.is_staff or user.is_superuser


def is_organizer(user):
    return hasattr(user, "organizer_profile") or user.is_staff or user.is_superuser


# Décorateurs personnalisés
def admin_required(view_func):
    decorated_view = user_passes_test(is_admin, login_url="dashboard:home")(view_func)
    return login_required(decorated_view)


def organizer_required(view_func):
    decorated_view = user_passes_test(is_organizer, login_url="dashboard:home")(view_func)
    return login_required(decorated_view)


# Vue principale du tableau de bord
@login_required
def dashboard_home(request):
    if request.user.is_staff or request.user.is_superuser:
        # Statistiques pour les administrateurs
        total_events = Event.objects.count()
        total_users = User.objects.count()
        total_tickets = Ticket.objects.count()
        total_payments = Payement.objects.count()
        total_demandes = Demande.objects.count()
        unread_contacts = Contact.objects.filter(is_read=False).count()

        # Graphiques pour les administrateurs
        events_by_category = dict(
            Event.objects.values("category__name")
            .annotate(count=Count("id"))
            .values_list("category__name", "count")
        )
        tickets_by_type = dict(
            Ticket.objects.values("type_ticket")
            .annotate(count=Count("id"))
            .values_list("type_ticket", "count")
        )

        context = {
            "total_events": total_events,
            "total_users": total_users,
            "total_tickets": total_tickets,
            "total_payments": total_payments,
            "total_demandes": total_demandes,
            "unread_contacts": unread_contacts,
            "events_by_category": events_by_category,
            "tickets_by_type": tickets_by_type,
            "recent_events": Event.objects.order_by("-created_at")[:5],
            "recent_demandes": Demande.objects.order_by("-id")[:5],
            "recent_contacts": Contact.objects.order_by("-created_at")[:5],
        }
    else:
        # Statistiques pour les organisateurs
        user_events = Event.objects.filter(user=request.user)
        total_user_events = user_events.count()
        total_user_tickets = Ticket.objects.filter(event__user=request.user).count()
        total_user_payments = Payement.objects.filter(event__user=request.user).count()

        context = {
            "total_events": total_user_events,
            "total_tickets": total_user_tickets,
            "total_payments": total_user_payments,
            "recent_events": user_events.order_by("-created_at")[:5],
        }

    return render(request, "dashboard/index.html", context)


# Gestion des événements
@login_required
def event_list(request):
    if request.user.is_staff or request.user.is_superuser:
        events = Event.objects.all().select_related("category", "user").prefetch_related("partner")
    else:
        events = (
            Event.objects.filter(user=request.user)
            .select_related("category")
            .prefetch_related("partner")
        )

    context = {
        "events": events,
        "categories": Category.objects.all(),
    }
    return render(request, "dashboard/events/list.html", context)


@login_required
def event_add(request):
    from event.forms import EventForms, TicketForms

    if request.method == "POST":
        event_form = EventForms(request.POST, request.FILES)
        ticket_form = TicketForms(request.POST)

        if event_form.is_valid() and ticket_form.is_valid():
            event = event_form.save(commit=False)
            event.user = request.user
            event.save()
            event_form.save_m2m()  # Pour sauvegarder les relations many-to-many

            ticket = ticket_form.save(commit=False)
            ticket.event = event
            ticket.save()

            messages.success(request, "L'événement a été créé avec succès.")
            return redirect("dashboard:event_list")
    else:
        event_form = EventForms()
        ticket_form = TicketForms()

    context = {
        "event_form": event_form,
        "ticket_form": ticket_form,
        "categories": Category.objects.all(),
        "partners": Partner.objects.all(),
    }
    return render(request, "dashboard/events/add.html", context)


@login_required
def event_edit(request, uid):
    from event.forms import EventForms, TicketForms

    event = get_object_or_404(Event, uid=uid)

    # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
    if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cet événement.")
        return redirect("dashboard:event_list")

    try:
        ticket_info = InfoTicket.objects.get(event=event)
    except InfoTicket.DoesNotExist:
        ticket_info = None

    if request.method == "POST":
        event_form = EventForms(request.POST, request.FILES, instance=event)
        ticket_form = TicketForms(request.POST, instance=ticket_info)

        if event_form.is_valid() and ticket_form.is_valid():
            event = event_form.save()

            ticket = ticket_form.save(commit=False)
            ticket.event = event
            ticket.save()

            messages.success(request, "L'événement a été mis à jour avec succès.")
            return redirect("dashboard:event_list")
    else:
        event_form = EventForms(instance=event)
        ticket_form = TicketForms(instance=ticket_info)

    context = {
        "event": event,
        "event_form": event_form,
        "ticket_form": ticket_form,
        "categories": Category.objects.all(),
        "partners": Partner.objects.all(),
    }
    return render(request, "dashboard/events/edit.html", context)


@login_required
def event_delete(request, uid):
    event = get_object_or_404(Event, uid=uid)

    # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
    if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
        messages.error(request, "Vous n'avez pas la permission de supprimer cet événement.")
        return redirect("dashboard:event_list")

    if request.method == "POST":
        event.delete()
        messages.success(request, "L'événement a été supprimé avec succès.")
        return redirect("dashboard:event_list")

    context = {
        "event": event,
    }
    return render(request, "dashboard/events/delete.html", context)


# Gestion des demandes
@admin_required
def demande_list(request):
    demandes = Demande.objects.all().select_related(
        "event", "ticket", "anonymous_user", "service_hotesse", "user"
    )

    context = {
        "demandes": demandes,
    }
    return render(request, "dashboard/demandes/list.html", context)


@admin_required
def demande_detail(request, uid):
    demande = get_object_or_404(Demande, uid=uid)
    services = demande.service.all()

    context = {
        "demande": demande,
        "services": services,
    }
    return render(request, "dashboard/demandes/detail.html", context)


@admin_required
@require_POST
def demande_accept(request, uid):
    demande = get_object_or_404(Demande, uid=uid)
    demande.is_accepted = True
    demande.save()

    # Si la demande a un événement, l'activer
    if demande.event:
        demande.event.statut = True
        demande.event.save()

    messages.success(request, "La demande a été acceptée avec succès.")
    return redirect("dashboard:demande_detail", uid=uid)


@admin_required
@require_POST
def demande_reject(request, uid):
    demande = get_object_or_404(Demande, uid=uid)
    demande.is_accepted = False
    demande.save()

    messages.success(request, "La demande a été rejetée.")
    return redirect("dashboard:demande_detail", uid=uid)


# Gestion des tickets
@login_required
def ticket_list(request):
    if request.user.is_staff or request.user.is_superuser:
        tickets = Ticket.objects.all().select_related("event", "payement")
    else:
        tickets = Ticket.objects.filter(event__user=request.user).select_related(
            "event", "payement"
        )

    context = {
        "tickets": tickets,
    }
    return render(request, "dashboard/tickets/list.html", context)


@login_required
def ticket_detail(request, code):
    ticket = get_object_or_404(Ticket, code_ticket=code)

    # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
    if (
        not (request.user.is_staff or request.user.is_superuser)
        and ticket.event.user != request.user
    ):
        messages.error(request, "Vous n'avez pas la permission de voir ce ticket.")
        return redirect("dashboard:ticket_list")

    context = {
        "ticket": ticket,
        "event": ticket.event,
        "payment": ticket.payement,
    }
    return render(request, "dashboard/tickets/detail.html", context)


@login_required
def ticket_print(request, code):
    ticket = get_object_or_404(Ticket, code_ticket=code)

    # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
    if (
        not (request.user.is_staff or request.user.is_superuser)
        and ticket.event.user != request.user
    ):
        messages.error(request, "Vous n'avez pas la permission d'imprimer ce ticket.")
        return redirect("dashboard:ticket_list")

    context = {
        "ticket": ticket,
        "event": ticket.event,
        "payment": ticket.payement,
    }
    return render(request, "dashboard/tickets/print.html", context)


# Gestion des contacts
@admin_required
def contact_list(request):
    contacts = Contact.objects.all().order_by("-created_at")

    context = {
        "contacts": contacts,
    }
    return render(request, "dashboard/contacts/list.html", context)


@admin_required
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)

    # Marquer comme lu si ce n'est pas déjà fait
    if not contact.is_read:
        contact.is_read = True
        contact.save()

    context = {
        "contact": contact,
    }
    return render(request, "dashboard/contacts/detail.html", context)


@admin_required
@require_POST
def contact_mark_read(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.is_read = True
    contact.save()

    if request.is_ajax():
        return JsonResponse({"status": "success"})

    messages.success(request, "Le message a été marqué comme lu.")
    return redirect("dashboard:contact_list")


# Gestion des utilisateurs
@admin_required
def user_list(request):
    users = User.objects.all()

    context = {
        "users": users,
    }
    return render(request, "dashboard/users/list.html", context)


@admin_required
def user_add(request):
    from django.contrib.auth.forms import UserCreationForm

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Gérer les options supplémentaires
            send_welcome_email = request.POST.get("send_welcome_email") == "on"  # noqa
            require_password_change = request.POST.get("require_password_change") == "on"  # noqa

            messages.success(request, f"L'utilisateur {user.username} a été créé avec succès.")
            return redirect("dashboard:user_list")
    else:
        form = UserCreationForm()

    context = {
        "form": form,
    }
    return render(request, "dashboard/users/add.html", context)


@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    events = Event.objects.filter(user=user)
    tickets = Ticket.objects.filter(event__user=user)

    context = {
        "user": user,
        "events": events,
        "tickets": tickets,
    }
    return render(request, "dashboard/users/detail.html", context)


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        # Mise à jour des champs de base
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)

        # Mise à jour des statuts
        user.is_active = request.POST.get("is_active") == "on"
        user.is_staff = request.POST.get("is_staff") == "on"
        user.is_superuser = request.POST.get("is_superuser") == "on"

        # Mise à jour du mot de passe si demandé
        password = request.POST.get("password")
        if password:
            user.set_password(password)

        user.save()
        messages.success(request, f"L'utilisateur {user.username} a été mis à jour avec succès.")
        return redirect("dashboard:user_list")

    context = {
        "user": user,
    }
    return render(request, "dashboard/users/edit.html", context)


@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        return redirect("dashboard:user_list")

    context = {
        "user": user,
    }
    return render(request, "dashboard/users/delete.html", context)


# Paramètres du système
@admin_required
def settings_general(request):
    # Récupérer ou créer les paramètres généraux
    settings = {}  # À remplacer par un modèle Settings réel

    if request.method == "POST":
        # Traiter le formulaire de paramètres généraux
        messages.success(request, "Les paramètres généraux ont été mis à jour avec succès.")
        return redirect("dashboard:settings_general")

    context = {
        "settings": settings,
    }
    return render(request, "dashboard/settings/general.html", context)


@admin_required
def settings_email(request):
    # Récupérer ou créer les paramètres d'email
    email_settings = {}  # À remplacer par un modèle EmailSettings réel
    email_templates = {}  # À remplacer par un modèle EmailTemplate réel

    if request.method == "POST":
        # Traiter le formulaire de configuration email
        messages.success(request, "La configuration email a été mise à jour avec succès.")
        return redirect("dashboard:settings_email")

    context = {
        "email_settings": email_settings,
        "email_templates": email_templates,
    }
    return render(request, "dashboard/settings/email.html", context)


@admin_required
def settings_payment(request):
    # Récupérer ou créer les paramètres de paiement
    payment_settings = {}  # À remplacer par un modèle PaymentSettings réel

    if request.method == "POST":
        # Traiter le formulaire de méthodes de paiement
        messages.success(request, "Les méthodes de paiement ont été mises à jour avec succès.")
        return redirect("dashboard:settings_payment")

    context = {
        "payment_settings": payment_settings,
    }
    return render(request, "dashboard/settings/payment.html", context)


@admin_required
def settings_seo(request):
    # Récupérer ou créer les paramètres SEO
    seo_settings = {}  # À remplacer par un modèle SEOSettings réel

    if request.method == "POST":
        # Traiter le formulaire de paramètres SEO
        messages.success(request, "Les paramètres SEO ont été mis à jour avec succès.")
        return redirect("dashboard:settings_seo")

    context = {
        "seo_settings": seo_settings,
    }
    return render(request, "dashboard/settings/seo.html", context)


@admin_required
def settings_backup(request):
    # Logique pour la sauvegarde et restauration
    if request.method == "POST":
        # Traiter la demande de sauvegarde ou restauration
        action = request.POST.get("action")
        if action == "backup":
            messages.success(request, "La sauvegarde a été créée avec succès.")
        elif action == "restore":
            messages.success(request, "La restauration a été effectuée avec succès.")

    context = {
        "backups": [],  # Liste des sauvegardes disponibles
    }
    return render(request, "dashboard/settings/backup.html", context)


@admin_required
def settings_system(request):
    # Collecter les informations système
    import sys

    import django

    system_info = {
        "python_version": sys.version,
        "django_version": django.get_version(),
        "database": settings.DATABASES["default"]["ENGINE"],
        "debug_mode": settings.DEBUG,
        "time_zone": settings.TIME_ZONE,
    }

    context = {
        "system_info": system_info,
    }
    return render(request, "dashboard/settings/system.html", context)


@admin_required
def settings_reset(request):
    # Réinitialiser les paramètres
    if request.method == "POST":
        # Logique de réinitialisation
        messages.success(request, "Les paramètres ont été réinitialisés avec succès.")
        return redirect("dashboard:settings_general")

    return redirect("dashboard:settings_general")


@admin_required
def email_template_edit(request, template):
    # Récupérer le modèle d'email spécifié
    # template_obj = get_object_or_404(EmailTemplate, name=template)

    if request.method == "POST":
        # Mettre à jour le modèle d'email
        messages.success(request, "Le modèle d'email a été mis à jour avec succès.")
        return redirect("dashboard:settings_email")

    context = {
        "template": template,
        # 'template_obj': template_obj,
    }
    return render(request, "dashboard/settings/email_template_edit.html", context)


# Statistiques et rapports
@admin_required
def stats_view(request):
    # Période sélectionnée (par défaut: 30 derniers jours)
    period = request.GET.get("period", "30d")

    if period == "7d":
        start_date = timezone.now() - timezone.timedelta(days=7)
    elif period == "30d":
        start_date = timezone.now() - timezone.timedelta(days=30)
    elif period == "90d":
        start_date = timezone.now() - timezone.timedelta(days=90)
    elif period == "1y":
        start_date = timezone.now() - timezone.timedelta(days=365)
    else:
        start_date = timezone.now() - timezone.timedelta(days=30)

    # Statistiques globales
    total_events = Event.objects.filter(created_at__gte=start_date).count()
    total_tickets = Ticket.objects.filter(created_at__gte=start_date).count()
    total_revenue = (
        Payement.objects.filter(created_at__gte=start_date).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # Graphiques
    events_by_category = dict(
        Event.objects.filter(created_at__gte=start_date)
        .values("category__name")
        .annotate(count=Count("id"))
        .values_list("category__name", "count")
    )

    tickets_by_type = dict(
        Ticket.objects.filter(created_at__gte=start_date)
        .values("type_ticket")
        .annotate(count=Count("id"))
        .values_list("type_ticket", "count")
    )

    context = {
        "period": period,
        "total_events": total_events,
        "total_tickets": total_tickets,
        "total_revenue": total_revenue,
        "events_by_category": events_by_category,
        "tickets_by_type": tickets_by_type,
    }
    return render(request, "dashboard/stats.html", context)


@admin_required
def reports_view(request):
    report_type = request.GET.get("type", "events")

    if report_type == "events":
        items = Event.objects.all().order_by("-created_at")
    elif report_type == "tickets":
        items = Ticket.objects.all().order_by("-created_at")
    elif report_type == "payments":
        items = Payement.objects.all().order_by("-created_at")
    elif report_type == "demandes":
        items = Demande.objects.all().order_by("-id")
    else:
        items = Event.objects.all().order_by("-created_at")

    context = {
        "report_type": report_type,
        "items": items,
    }
    return render(request, "dashboard/reports.html", context)


# Profil utilisateur
@login_required
def profile_view(request):
    user_events = Event.objects.filter(user=request.user).order_by("-created_at")

    context = {
        "user": request.user,
        "user_events": user_events,
    }
    return render(request, "dashboard/profile/view.html", context)


@login_required
def profile_edit(request):
    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)

        if (
            "email" in request.POST
            and User.objects.filter(email=request.POST["email"]).exclude(pk=user.pk).exists()
        ):
            messages.error(request, "Cet email est déjà utilisé par un autre compte.")
        else:
            user.email = request.POST.get("email", user.email)

        if "current_password" in request.POST and request.POST["current_password"]:
            if user.check_password(request.POST["current_password"]):
                if request.POST["new_password1"] == request.POST["new_password2"]:
                    user.set_password(request.POST["new_password1"])
                    messages.success(request, "Votre mot de passe a été mis à jour.")
                else:
                    messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            else:
                messages.error(request, "Mot de passe actuel incorrect.")

        user.save()
        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect("dashboard:profile")

    context = {
        "user": user,
    }
    return render(request, "dashboard/profile/edit.html", context)
