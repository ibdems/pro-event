from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from event.models import Event, Ticket


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux administrateurs"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class TicketListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des tickets"""

    model = Ticket
    template_name = "dashboard/tickets/list.html"
    context_object_name = "tickets"

    def get_queryset(self):
        queryset = Ticket.objects.select_related("event", "payement")

        # Filtrer par utilisateur si pas admin
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(event__user=self.request.user)

        # Appliquer les filtres

        event_search = self.request.GET.get("event_search")
        if event_search:
            queryset = queryset.filter(event__title__icontains=event_search)

        event_type = self.request.GET.get("event_type")
        if event_type:
            queryset = queryset.filter(event__type_event=event_type)

        ticket_type = self.request.GET.get("type")
        if ticket_type:
            queryset = queryset.filter(type_ticket=ticket_type)

        status = self.request.GET.get("status")
        if status == "paid":
            queryset = queryset.filter(payement__statut_payement=True)
        elif status == "pending":
            queryset = queryset.filter(payement__statut_payement=False)

        purchase_date = self.request.GET.get("date")
        if purchase_date:
            queryset = queryset.filter(created_at__date=purchase_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Liste des événements pour le filtre
        if self.request.user.is_staff or self.request.user.is_superuser:
            context["events"] = Event.objects.all()
        else:
            context["events"] = Event.objects.filter(user=self.request.user)

        # Statistiques
        tickets = self.get_queryset()
        context["total_tickets"] = tickets.count()

        # Calculer les revenus (8% du prix des tickets)
        total_revenue = 0
        for ticket in tickets:
            if ticket.event.infoticket_event:
                if ticket.type_ticket == "normal":
                    price = ticket.event.infoticket_event.prix_normal
                elif ticket.type_ticket == "vip":
                    price = ticket.event.infoticket_event.prix_vip
                elif ticket.type_ticket == "vvip":
                    price = ticket.event.infoticket_event.prix_vvip
                else:
                    price = 0
            else:
                price = ticket.payement.amount

            total_revenue += price * 0.08  # 8% du prix

        context["total_revenue"] = total_revenue

        # Ticket moyen (commission moyenne)
        context["average_ticket"] = total_revenue / tickets.count() if tickets.count() > 0 else 0

        # Taux de conversion (tickets payés / total)
        paid_tickets = tickets.filter(payement__statut_payement=True).count()
        context["conversion_rate"] = (
            (paid_tickets / tickets.count() * 100) if tickets.count() > 0 else 0
        )

        # Date courante pour comparer avec la date de fin d'événement
        context["now"] = timezone.now()

        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un ticket"""

    model = Ticket
    template_name = "dashboard/tickets/detail.html"
    context_object_name = "ticket"
    slug_field = "code_ticket"
    slug_url_kwarg = "code"

    def get_object(self, queryset=None):
        return get_object_or_404(Ticket, code_ticket=self.kwargs.get(self.slug_url_kwarg))

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if (
            not (request.user.is_staff or request.user.is_superuser)
            and ticket.event.user != request.user
        ):
            messages.error(request, "Vous n'avez pas la permission de voir ce ticket.")
            return redirect("dashboard:ticket_list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.get_object()

        # Infos sur l'événement et le paiement
        context["event"] = ticket.event
        context["payment"] = ticket.payement

        # Statistiques de l'événement
        total_sold = Ticket.objects.filter(event=ticket.event).count()

        # Calculer le total des revenus (8% des prix des tickets)
        revenue = 0
        for t in Ticket.objects.filter(event=ticket.event):
            if t.type_ticket == "normal":
                price = (
                    ticket.event.infoticket_event.prix_normal
                    if ticket.event.infoticket_event
                    else 0
                )
            elif t.type_ticket == "vip":
                price = (
                    ticket.event.infoticket_event.prix_vip if ticket.event.infoticket_event else 0
                )
            elif t.type_ticket == "vvip":
                price = (
                    ticket.event.infoticket_event.prix_vvip if ticket.event.infoticket_event else 0
                )
            else:
                price = 0

            revenue += price

        # Commission de 8%
        commission = revenue * 0.08

        # Capacité totale
        total_capacity = 0
        if ticket.event.infoticket_event:
            total_capacity = (
                ticket.event.infoticket_event.normal_capacity
                + ticket.event.infoticket_event.vip_capacity
                + ticket.event.infoticket_event.vvip_capacity
            )

        context["ticket_stats"] = {
            "total_sold": total_sold,
            "tickets_left": max(0, total_capacity - total_sold),
            "revenue": revenue,
            "commission": commission,
        }

        # Date courante pour comparer avec la date de fin d'événement
        context["now"] = timezone.now()

        return context


class TicketPrintView(LoginRequiredMixin, DetailView):
    """Vue pour imprimer un ticket"""

    model = Ticket
    template_name = "dashboard/tickets/print.html"
    context_object_name = "ticket"
    slug_field = "code_ticket"
    slug_url_kwarg = "code"

    def get_object(self, queryset=None):
        return get_object_or_404(Ticket, code_ticket=self.kwargs.get(self.slug_url_kwarg))

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if (
            not (request.user.is_staff or request.user.is_superuser)
            and ticket.event.user != request.user
        ):
            messages.error(request, "Vous n'avez pas la permission d'imprimer ce ticket.")
            return redirect("dashboard:ticket_list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.get_object()
        context["event"] = ticket.event
        context["payment"] = ticket.payement
        return context


class TicketSendEmailView(LoginRequiredMixin, View):
    """Vue pour envoyer un ticket par email"""

    def post(self, request, *args, **kwargs):
        payement_id = kwargs.get("payement_id")
        ticket_id = kwargs.get("ticket_id")

        # On peut envoyer par ID de ticket ou ID de paiement
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            if (
                not (request.user.is_staff or request.user.is_superuser)
                and ticket.event.user != request.user
            ):
                messages.error(request, "Vous n'avez pas la permission d'envoyer ce ticket.")
                return redirect("dashboard:ticket_list")

            payement_id = ticket.payement.id
            tickets = [ticket]
        elif payement_id:
            # Vérifier l'accès aux tickets associés à ce paiement
            tickets = Ticket.objects.filter(payement_id=payement_id)
            if not tickets.exists():
                messages.error(request, "Aucun ticket trouvé pour ce paiement.")
                return redirect("dashboard:ticket_list")

            if (
                not (request.user.is_staff or request.user.is_superuser)
                and tickets.first().event.user != request.user
            ):
                messages.error(request, "Vous n'avez pas la permission d'envoyer ces tickets.")
                return redirect("dashboard:ticket_list")
        else:
            messages.error(request, "Ticket ou paiement non spécifié.")
            return redirect("dashboard:ticket_list")

        # Vérifier si chaque ticket a déjà un PDF, sinon le générer
        from celery import chord, group
        from django.db import transaction

        from event.tasks import generate_and_save_ticket_pdf, send_ticket_by_email

        tasks = []
        with transaction.atomic():
            for ticket in tickets:
                if not ticket.ticket_pdf:
                    # Ajouter une tâche pour générer le PDF du ticket
                    tasks.append(
                        generate_and_save_ticket_pdf.s(ticket.event.id, ticket.id, payement_id)
                    )

        # Si des tâches de génération de PDF sont nécessaires, les exécuter avant l'envoi
        if tasks:

            def send_email_after_pdfs():
                callback = send_ticket_by_email.si(payement_id)
                chord(group(tasks))(callback)

            transaction.on_commit(send_email_after_pdfs)
            messages.success(
                request, "Les tickets seront générés puis envoyés par email dans quelques instants."
            )
        else:
            # Tous les PDFs existent déjà, envoyer directement les tickets
            send_ticket_by_email.delay(payement_id)
            messages.success(
                request, "Les tickets seront envoyés par email dans quelques instants."
            )

        # Rediriger vers la page appropriée
        if ticket_id:
            return redirect(
                reverse("dashboard:ticket_detail", kwargs={"code": tickets[0].code_ticket})
            )
        return redirect("dashboard:ticket_list")


class TicketMarkPaidView(LoginRequiredMixin, View):
    """Vue pour marquer un ticket comme payé"""

    def post(self, request, *args, **kwargs):
        code = kwargs.get("code")
        ticket = get_object_or_404(Ticket, code_ticket=code)

        # Vérifier que l'utilisateur est propriétaire de l'événement ou admin
        if (
            not (request.user.is_staff or request.user.is_superuser)
            and ticket.event.user != request.user
        ):
            messages.error(request, "Vous n'avez pas la permission de modifier ce ticket.")
            return redirect("dashboard:ticket_list")

        # Marquer le paiement comme effectué
        ticket.payement.statut_payement = True
        ticket.payement.updated_at = timezone.now()
        ticket.payement.save()

        messages.success(request, "Le ticket a été marqué comme payé avec succès.")

        # Rediriger vers la page de détail
        return redirect(reverse("dashboard:ticket_detail", kwargs={"code": code}))
