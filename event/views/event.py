from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView

from event.filter import EventFilter
from event.forms import PayementForm
from event.models import Event, InfoTicket
from event.utils import create_paycard_payment


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

                    # Création du paiement (mais pas de tickets)
                    payement = form.save(commit=False)
                    payement.event = event
                    info_ticket = event.infoticket_event

                    # Sauvegarder les quantités
                    payement.quantity_normal = quantities["normal"]
                    payement.quantity_vip = quantities["vip"]
                    payement.quantity_vvip = quantities["vvip"]

                    payement.amount = (
                        (quantities["normal"] * info_ticket.prix_normal)
                        + (quantities["vip"] * info_ticket.prix_vip)
                        + (quantities["vvip"] * info_ticket.prix_vvip)
                    )
                    payement.quantity = sum(quantities.values())

                    # Assigner manuellement les champs non mappés du formulaire au modèle
                    payement.email_reception = data.get("email_reception")
                    payement.telephone_reception = data.get("telephone_reception")

                    # Toujours initier le paiement externe (Orange, Paycard, Visa, MTN MoMo)
                    montant = payement.amount
                    description = f"Paiement pour l'événement {event.title}"
                    payment_method = data.get("payment_method")
                    result, reference = create_paycard_payment(
                        request, montant, description, payment_method
                    )
                    if result.get("code") == 0:
                        payement.operation_reference = reference
                        payement.statut_payement = "en_attente"
                        payement.save()
                        return redirect(result["payment_url"])
                    else:
                        error_msg = result.get(
                            "error_message", "Erreur lors de la création du paiement."
                        )
                        messages.error(request, error_msg)
                        return self.render_to_response(self.get_context_data(form=form))

            except Exception:
                messages.error(request, "Une erreur est survenue")
                return self.render_to_response(self.get_context_data(form=form))

        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        context["disponibilite"] = event.get_disponibilite()
        context["nombre_ticket_dispo"] = event.total_tickets_disponibles()

        if "form" not in kwargs:
            context["form"] = PayementForm()
        return context
