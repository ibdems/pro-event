import csv
import io
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from event.forms import CategoryForms, EventForms, PartnerForms, TicketForms
from event.models import Category, Event, InfoTicket, Invitation, Partner
from event.tasks import send_invitation_email


class AdminOrOrganizerRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs ou aux organisateurs de l'événement"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class EventListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des événements"""

    model = Event
    template_name = "dashboard/events/list.html"
    context_object_name = "events"

    def get_queryset(self):
        queryset = (
            Event.objects.all().select_related("category", "user").prefetch_related("partner")
        )

        # Restreindre aux événements de l'utilisateur s'il n'est pas staff
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user=self.request.user)

        # Appliquer les filtres
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(statut=(status == "1"))

        type_event = self.request.GET.get("type_event")
        if type_event:
            queryset = queryset.filter(type_event=type_event)

        title = self.request.GET.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        date_from = self.request.GET.get("date_from")
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                queryset = queryset.filter(start_date__gte=date_from_obj)
            except (ValueError, TypeError):
                pass

        date_to = self.request.GET.get("date_to")
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                # Ajouter 23:59:59 pour inclure toute la journée
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(start_date__lte=date_to_obj)
            except (ValueError, TypeError):
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class EventAddView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter un nouvel événement"""

    template_name = "dashboard/events/add.html"
    success_url = reverse_lazy("dashboard:event_list")

    def get_form_class(self):
        return EventForms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" in context:
            context["event_form"] = context.pop("form")
        if "ticket_form" not in context:
            context["ticket_form"] = TicketForms()
        context["categories"] = Category.objects.all()
        context["partners"] = Partner.objects.all()
        return context

    def form_valid(self, form):
        event_form = form
        ticket_form = TicketForms(self.request.POST)

        if event_form.is_valid() and ticket_form.is_valid():
            event = event_form.save(commit=False)
            event.user = self.request.user
            event.save()
            event_form.save_m2m()  # Pour sauvegarder les relations many-to-many

            ticket = ticket_form.save(commit=False)
            ticket.event = event
            ticket.save()

            messages.success(self.request, "L'événement a été créé avec succès.")
            return redirect(self.success_url)
        else:
            context = self.get_context_data()
            context["event_form"] = event_form
            context["ticket_form"] = ticket_form
            return self.render_to_response(context)


class EventEditView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un événement existant"""

    model = Event
    template_name = "dashboard/events/edit.html"
    success_url = reverse_lazy("dashboard:event_list")
    form_class = EventForms
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        return get_object_or_404(Event, uid=self.kwargs.get(self.pk_url_kwarg))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(request, "Vous n'avez pas la permission de modifier cet événement.")
            return redirect("dashboard:event_list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()

        if "form" in context:
            context["event_form"] = context.pop("form")

        try:
            ticket_info = InfoTicket.objects.get(event=event)
        except InfoTicket.DoesNotExist:
            ticket_info = None

        if "ticket_form" not in context:
            context["ticket_form"] = TicketForms(instance=ticket_info)

        context["categories"] = Category.objects.all()
        context["partners"] = Partner.objects.all()
        return context

    def form_valid(self, form):
        event_form = form
        event = self.get_object()

        try:
            ticket_info = InfoTicket.objects.get(event=event)
        except InfoTicket.DoesNotExist:
            ticket_info = None

        ticket_form = TicketForms(self.request.POST, instance=ticket_info)

        if event_form.is_valid() and ticket_form.is_valid():
            event = event_form.save()

            ticket = ticket_form.save(commit=False)
            ticket.event = event
            ticket.save()

            messages.success(self.request, "L'événement a été mis à jour avec succès.")
            return redirect(self.success_url)
        else:
            context = self.get_context_data()
            context["event_form"] = event_form
            context["ticket_form"] = ticket_form
            return self.render_to_response(context)


class EventDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un événement"""

    model = Event
    template_name = "dashboard/events/detail.html"
    context_object_name = "event"
    pk_url_kwarg = "uid"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if (
            not (request.user.is_staff or request.user.is_superuser)
            and self.object.user != request.user
        ):
            messages.error(request, "Vous n'avez pas la permission de gérer cet événement.")
            return redirect("dashboard:event_list")

        # Traitement des actions pour les invitations si on est sur la page des invitations
        if self.template_name == "dashboard/events/invitations.html":
            delete_id = request.GET.get("delete")
            resend_id = request.GET.get("resend")

            if delete_id:
                try:
                    invitation = Invitation.objects.get(id=delete_id, event=self.object)
                    invitation.delete()
                    messages.success(request, "L'invitation a été supprimée avec succès.")
                    return redirect("dashboard:event_invitations", uid=self.object.uid)
                except Invitation.DoesNotExist:
                    messages.error(request, "L'invitation demandée n'existe pas.")

            if resend_id:
                try:
                    invitation = Invitation.objects.get(
                        id=resend_id, event=self.object, status="pending"
                    )

                    # Réinitialiser la date d'envoi pour indiquer un nouvel envoi
                    invitation.sent_at = None
                    invitation.save()

                    # Envoyer l'invitation
                    send_invitation_email.delay(invitation.id)

                    messages.success(
                        request, f"L'invitation a été renvoyée à {invitation.email} avec succès."
                    )
                    return redirect("dashboard:event_invitations", uid=self.object.uid)
                except Invitation.DoesNotExist:
                    messages.error(
                        request, "L'invitation demandée n'existe pas ou ne peut pas être renvoyée."
                    )

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Event, uid=self.kwargs.get(self.pk_url_kwarg))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        context["tickets"] = self.object.ticket_event.all().order_by("-created_at")[:5]

        # Si nous sommes sur la page des invitations, ajoutons les données nécessaires
        if self.template_name == "dashboard/events/invitations.html":
            invitations = self.object.invitations.all().order_by("-created_at")
            context["invitations"] = invitations

            # Statistiques des invitations
            total = invitations.count()

            if total > 0:
                accepted = invitations.filter(status="accepted").count()
                declined = invitations.filter(status="declined").count()
                pending = invitations.filter(status="pending").count()

                context["stats"] = {
                    "total": total,
                    "accepted": accepted,
                    "declined": declined,
                    "pending": pending,
                    "accepted_percent": round((accepted / total) * 100) if total > 0 else 0,
                    "declined_percent": round((declined / total) * 100) if total > 0 else 0,
                    "pending_percent": round((pending / total) * 100) if total > 0 else 0,
                }
            else:
                context["stats"] = {
                    "total": 0,
                    "accepted": 0,
                    "declined": 0,
                    "pending": 0,
                    "accepted_percent": 0,
                    "declined_percent": 0,
                    "pending_percent": 0,
                }

            # Ajouter une pagination pour les invitations
            page = self.request.GET.get("page", 1)
            paginator = Paginator(invitations, 20)  # 20 invitations par page

            try:
                invitations_page = paginator.page(page)
            except PageNotAnInteger:
                invitations_page = paginator.page(1)
            except EmptyPage:
                invitations_page = paginator.page(paginator.num_pages)

            context["invitations"] = invitations_page
            context["is_paginated"] = True
            context["page_obj"] = invitations_page

        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un événement"""

    model = Event
    template_name = "dashboard/events/delete.html"
    success_url = reverse_lazy("dashboard:event_list")
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        return get_object_or_404(Event, uid=self.kwargs.get(self.pk_url_kwarg))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(request, "Vous n'avez pas la permission de supprimer cet événement.")
            return redirect("dashboard:event_list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "L'événement a été supprimé avec succès.")
        return redirect(self.success_url)


class EventActivateView(LoginRequiredMixin, View):
    """Vue pour activer un événement"""

    def get_object(self, queryset=None):
        return get_object_or_404(Event, uid=self.kwargs.get("uid"))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(request, "Vous n'avez pas la permission d'activer cet événement.")
            return redirect("dashboard:event_list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        event.statut = True
        event.save()
        messages.success(request, "L'événement a été activé avec succès.")
        return redirect("dashboard:event_detail", uid=event.uid)


class EventDeactivateView(LoginRequiredMixin, View):
    """Vue pour désactiver un événement"""

    def get_object(self, queryset=None):
        return get_object_or_404(Event, uid=self.kwargs.get("uid"))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(request, "Vous n'avez pas la permission de désactiver cet événement.")
            return redirect("dashboard:event_list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        event.statut = False
        event.save()
        messages.success(request, "L'événement a été désactivé avec succès.")
        return redirect("dashboard:event_detail", uid=event.uid)


class CategoryListView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, ListView):
    """Vue pour afficher la liste des catégories"""

    model = Category
    template_name = "dashboard/categories/list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.all().annotate(event_count=Count("event"))


class CategoryAddView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, CreateView):
    """Vue pour ajouter une nouvelle catégorie"""

    model = Category
    form_class = CategoryForms
    template_name = "dashboard/categories/add.html"
    success_url = reverse_lazy("dashboard:category_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "La catégorie a été créée avec succès.")
        return response


class CategoryEditView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, UpdateView):
    """Vue pour modifier une catégorie existante"""

    model = Category
    form_class = CategoryForms
    template_name = "dashboard/categories/edit.html"
    success_url = reverse_lazy("dashboard:category_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "La catégorie a été modifiée avec succès.")
        return response


class CategoryDeleteView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, DeleteView):
    """Vue pour supprimer une catégorie"""

    model = Category
    template_name = "dashboard/categories/delete.html"
    success_url = reverse_lazy("dashboard:category_list")

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception:
            messages.error(
                request,
                "Impossible de supprimer cette catégorie car elle est "
                "utilisée par des événements.",
            )
            return redirect(self.success_url)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "La catégorie a été supprimée avec succès.")
        return redirect(success_url)


class PartnerListView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, ListView):
    """Vue pour afficher la liste des partenaires"""

    model = Partner
    template_name = "dashboard/partners/list.html"
    context_object_name = "partners"

    def get_queryset(self):
        return Partner.objects.all().annotate(event_count=Count("event_partner"))


class PartnerAddView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, CreateView):
    """Vue pour ajouter un nouveau partenaire"""

    model = Partner
    form_class = PartnerForms
    template_name = "dashboard/partners/add.html"
    success_url = reverse_lazy("dashboard:partner_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_staff:
            form.instance.is_platform_partner = True
        form.save()
        messages.success(self.request, "Le partenaire a été créé avec succès.")
        return response


class PartnerEditView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, UpdateView):
    """Vue pour modifier un partenaire existant"""

    model = Partner
    form_class = PartnerForms
    template_name = "dashboard/partners/edit.html"
    success_url = reverse_lazy("dashboard:partner_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_staff:
            form.instance.is_platform_partner = True
        form.save()
        messages.success(self.request, "Le partenaire a été modifié avec succès.")
        return response


class PartnerDeleteView(LoginRequiredMixin, AdminOrOrganizerRequiredMixin, DeleteView):
    """Vue pour supprimer un partenaire"""

    model = Partner
    template_name = "dashboard/partners/delete.html"
    success_url = reverse_lazy("dashboard:partner_list")

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            messages.error(
                request,
                f"Impossible de supprimer ce partenaire car il est utilisé par des événements. {e}",
            )
            return redirect(self.success_url)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "Le partenaire a été supprimé avec succès.")
        return redirect(success_url)


class EventSendInvitationView(LoginRequiredMixin, View):
    """Vue pour envoyer une invitation individuelle"""

    def get_event(self):
        return get_object_or_404(Event, uid=self.kwargs.get("uid"))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_event()
        # Vérifier que l'événement est privé
        if not event.type_event:
            messages.error(
                request, "Impossible d'envoyer des invitations pour un événement public."
            )
            return redirect("dashboard:event_detail", uid=event.uid)

        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(
                request,
                "Vous n'avez pas la permission d'envoyer des invitations pour cet événement.",
            )
            return redirect("dashboard:event_list")

        # Vérifier s'il y a une demande de renvoi d'invitation
        resend_id = request.GET.get("resend")
        if resend_id:
            try:
                invitation = Invitation.objects.get(id=resend_id, event=event)
                # Réinitialiser la date d'envoi pour indiquer un nouvel envoi
                invitation.sent_at = None
                invitation.save()

                # Envoyer l'invitation
                send_invitation_email.delay(invitation.id)

                messages.success(
                    request, f"L'invitation a été renvoyée à {invitation.email} avec succès."
                )
                return redirect("dashboard:event_detail", uid=event.uid)
            except Invitation.DoesNotExist:
                messages.error(
                    request, "L'invitation demandée n'existe pas ou ne peut pas être renvoyée."
                )
                return redirect("dashboard:event_detail", uid=event.uid)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        event = self.get_event()
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message", "")
        ticket_type = request.POST.get("ticket_type", "normal")
        send_now = request.POST.get("send_now") == "on"

        if not name or not email:
            messages.error(request, "Le nom et l'email sont obligatoires.")
            return redirect("dashboard:event_detail", uid=event.uid)

        # Créer l'invitation
        invitation = Invitation.objects.create(
            event=event, name=name, email=email, message=message, ticket_type=ticket_type
        )

        # Envoyer l'invitation immédiatement si demandé
        if send_now:
            send_invitation_email.delay(invitation.id)
            messages.success(request, f"L'invitation a été envoyée à {email}.")
        else:
            messages.success(
                request, f"L'invitation a été créée pour {email} mais n'a pas encore été envoyée."
            )

        return redirect("dashboard:event_detail", uid=event.uid)


class EventImportInvitationsView(LoginRequiredMixin, View):
    """Vue pour importer des invitations en masse depuis un CSV"""

    def get_event(self):
        return get_object_or_404(Event, uid=self.kwargs.get("uid"))

    def dispatch(self, request, *args, **kwargs):
        event = self.get_event()
        # Vérifier que l'événement est privé
        if not event.type_event:
            messages.error(
                request, "Impossible d'envoyer des invitations pour un événement public."
            )
            return redirect("dashboard:event_detail", uid=event.uid)

        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if not (request.user.is_staff or request.user.is_superuser) and event.user != request.user:
            messages.error(
                request,
                "Vous n'avez pas la permission d'envoyer des invitations pour cet événement.",
            )
            return redirect("dashboard:event_list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        event = self.get_event()
        csv_file = request.FILES.get("invitation_csv")
        common_message = request.POST.get("message", "")
        send_now = request.POST.get("send_now") == "on"

        if not csv_file:
            messages.error(request, "Aucun fichier CSV n'a été fourni.")
            return redirect("dashboard:event_detail", uid=event.uid)

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Le fichier doit être au format CSV.")
            return redirect("dashboard:event_detail", uid=event.uid)

        # Traiter le fichier CSV
        try:
            decoded_file = csv_file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            next(reader)  # Ignorer l'en-tête

            invites_count = 0
            for row in reader:
                if len(row) < 2 or not row[0] or not row[1]:
                    continue  # Ignorer les lignes incomplètes

                name = row[0]
                email = row[1]
                ticket_type = (
                    row[2] if len(row) > 2 and row[2] in ["normal", "vip", "vvip"] else "normal"
                )

                # Créer l'invitation
                invitation = Invitation.objects.create(
                    event=event,
                    name=name,
                    email=email,
                    message=common_message,
                    ticket_type=ticket_type,
                )

                # Envoyer l'invitation immédiatement si demandé
                if send_now:
                    send_invitation_email.delay(invitation.id)

                invites_count += 1

            if send_now:
                messages.success(
                    request, f"{invites_count} invitations ont été importées et envoyées."
                )
            else:
                messages.success(
                    request,
                    f"{invites_count} invitations ont été importées mais n'ont pas"
                    " encore été envoyées.",
                )

        except Exception as e:
            messages.error(
                request, f"Une erreur s'est produite lors de l'importation du fichier CSV: {str(e)}"
            )

        return redirect("dashboard:event_detail", uid=event.uid)


class EventDownloadInvitationTemplateView(LoginRequiredMixin, View):
    """Vue pour télécharger le modèle CSV d'invitation"""

    def get(self, request, *args, **kwargs):
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="modele_invitations.csv"'

        writer = csv.writer(response)
        writer.writerow(["Nom", "Email", "Type de ticket (normal, vip, vvip)"])
        writer.writerow(["Jean Dupont", "jean.dupont@example.com", "normal"])
        writer.writerow(["Marie Martin", "marie.martin@example.com", "vip"])

        return response
