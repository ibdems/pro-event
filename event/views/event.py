from celery import chord, group
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView

from event.filter import EventFilter
from event.forms import PayementForm
from event.models import Event, InfoTicket, Ticket
from event.tasks import (
    generate_and_save_ticket_pdf,
    send_ticket_by_email,
    send_ticket_by_whatsapp,
)


class EventView(FilterView, ListView):
    model = Event
    template_name = "event/event.html"
    context_object_name = "events"
    paginate_by = 9
    filterset_class = EventFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "event"
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs.filter(statut=True)
            .only(
                "uid",
                "category",
                "title",
                "start_date",
                "end_date",
                "location",
                "image",
            )
            .select_related("category")
            .prefetch_related(
                Prefetch("infoticket_event", queryset=InfoTicket.objects.only("type_access"))
            )
            .order_by("-created_at")
        )


class DetailEventView(DetailView):
    pk_url_kwarg = "uid"
    model = Event
    context_object_name = "event"
    template_name = "event/event_detail.html"

    def get_object(self, queryset=None):
        return (
            Event.objects.select_related("category", "user", "infoticket_event")
            .prefetch_related("partner")
            .get(uid=self.kwargs.get("uid"))
        )

    def post(self, request, *args, **kwargs):
        form = PayementForm(request.POST)
        self.object = self.get_object()

        if form.is_valid():
            try:
                with transaction.atomic():
                    data = form.cleaned_data
                    event = self.object
                    contact_method = data.get("contact_method", "email")

                    # Récupération des quantités
                    quantities = {
                        "normal": int(data.get("quantity_normal", 0)),
                        "vip": int(data.get("quantity_vip", 0)),
                        "vvip": int(data.get("quantity_vvip", 0)),
                    }

                    # Vérification de la disponibilité pour chaque type
                    for type_ticket, quantite in quantities.items():
                        if quantite > 0 and not event.verifier_disponibilite(type_ticket, quantite):
                            dispo = event.get_disponibilite()[type_ticket]["disponibles"]
                            messages.error(
                                request,
                                f"Il ne reste que {dispo} tickets {type_ticket} disponibles",
                            )
                            return redirect("event:event_detail", uid=event.uid)

                    # Création du paiement
                    payement = form.save(commit=False)
                    payement.event = event
                    info_ticket = event.infoticket_event
                    payement.amount = (
                        (quantities["normal"] * info_ticket.prix_normal)
                        + (quantities["vip"] * info_ticket.prix_vip)
                        + (quantities["vvip"] * info_ticket.prix_vvip)
                    )
                    payement.quantity = sum(quantities.values())
                    payement.save()

                    # Création des tickets
                    tasks = []
                    for type_ticket, quantite in quantities.items():
                        if quantite > 0:
                            for _ in range(quantite):
                                ticket = Ticket.objects.create(
                                    payement=payement, event=event, type_ticket=type_ticket
                                )
                                tasks.append(
                                    generate_and_save_ticket_pdf.s(event.id, ticket.id, payement.id)
                                )

                    def send_email_after_commit():
                        if contact_method == "email":
                            callback = send_ticket_by_email.si(payement.id)
                        else:
                            callback = send_ticket_by_whatsapp.si(payement.id)
                        chord(group(tasks))(callback)

                    transaction.on_commit(send_email_after_commit)

                    messages.success(
                        request,
                        "Votre paiement a été effectué avec succès. "
                        "Vous recevrez vos billets par email/WhatsApp dans quelques instants.",
                    )
                    return redirect("event:event_detail", uid=event.uid)

            except Exception:
                messages.error(request, "Une erreur est survenue")
                return self.render_to_response(self.get_context_data(form=form))

        messages.error(request, "Une erreur s'est produite lors du paiement.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        context["disponibilite"] = event.get_disponibilite()
        context["nombre_ticket_dispo"] = event.total_tickets_disponibles()

        if "form" not in kwargs:
            context["form"] = PayementForm()
        return context
