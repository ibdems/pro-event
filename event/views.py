from django.contrib import messages
from django.db import transaction
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django_filters.views import FilterView

from .filter import EventFilter
from .forms import ContactForm, EventForms, PayementForm
from .models import Contact, Event, Ticket
from .utils import save_ticket_pdf, send_ticket_by_email


class HomeView(ListView):
    model = Event
    template_name = "event/accueil.html"
    context_object_name = "events"

    def get_queryset(self):
        qr = super().get_queryset()
        return qr.filter(statut=True).order_by("-created_at")[:3]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "home"
        return context


class AboutView(TemplateView):
    template_name = "event/apropos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "about"
        return context


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

    def get_ordering(self):
        order = super().get_ordering()
        return order or "-created_at"


class TicketView(TemplateView):
    template_name = "event/ticket_vertical.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupération de l'événement "Seminaire test"
        event = Event.objects.filter(title="Mariage de Dems").first()
        if not event:
            raise Http404("L'événement 'Seminaire test' n'existe pas.")

        # Récupération d'un ticket lié à l'événement
        ticket = Ticket.objects.filter(event=event).first()
        if not ticket:
            raise Http404("Aucun ticket disponible pour cet événement.")

        # Récupération du paiement associé au ticket
        payement = ticket.payement

        # Ajout des données au contexte
        context["event"] = event
        context["ticket"] = ticket
        context["payement"] = payement

        return context


class DetailEventView(DetailView):
    pk_url_kwarg = "uid"
    model = Event
    context_object_name = "event"
    template_name = "event/event_detail.html"

    def get_object(self, queryset=None):
        return (
            Event.objects.select_related("category", "user")
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
                    quantity_normal = int(data.get("quantity_normal", 0))
                    quantity_vip = int(data.get("quantity_vip", 0))
                    quantity_vvip = int(data.get("quantity_vvip", 0))

                    if quantity_normal > event.normal_capacity:
                        raise ValidationError("Pas assez de tickets Normaux disponibles.")
                    if quantity_vip > event.vip_capacity:
                        raise ValidationError("Pas assez de tickets VIP disponibles.")
                    if quantity_vvip > event.vvip_capacity:
                        raise ValidationError("Pas assez de tickets VVIP disponibles.")

                    payement = form.save(commit=False)
                    payement.event = event
                    payement.amount = (
                        (quantity_normal * event.prix_normal)
                        + (quantity_vip * event.prix_vip)
                        + (quantity_vvip * event.prix_vvip)
                    )
                    payement.quantity = quantity_normal + quantity_vip + quantity_vvip
                    payement.save()

                    tickets = []
                    for _ in range(quantity_normal):
                        ticket = Ticket.objects.create(
                            payement=payement, event=event, type_ticket="normal"
                        )
                        save_ticket_pdf(ticket, event, payement)
                        tickets.append(ticket)

                    for _ in range(quantity_vip):
                        ticket = Ticket.objects.create(
                            payement=payement, event=event, type_ticket="vip"
                        )
                        save_ticket_pdf(ticket, event, payement)
                        tickets.append(ticket)

                    for _ in range(quantity_vvip):
                        ticket = Ticket.objects.create(
                            payement=payement, event=event, type_ticket="vvip"
                        )
                        save_ticket_pdf(ticket, event, payement)
                        tickets.append(ticket)
                    print(tickets)

                    send_ticket_by_email(payement, tickets)

                    messages.success(
                        request,
                        "Votre payement a été effectué avec succès.\n"
                        "Vous recevrez le/les ticket(s) dans l'option de reception choisi.",
                    )
                    return redirect("event:event_detail", uid=event.uid)
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Une erreur s'est produite lors du payement.")
            # Passez le formulaire avec ses erreurs au contexte
            return self.render_to_response(self.get_context_data(form=form))

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajoutez le formulaire au contexte si non inclus
        if "form" not in kwargs:
            context["form"] = PayementForm()
        return context


class ContactView(CreateView):
    template_name = "event/contact.html"
    model = Contact
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contact"
        return context


class EventAddView(CreateView):
    template_name = "event/event_add.html"
    model = Event
    form_class = EventForms
    success_url = "/event/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "event"
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
