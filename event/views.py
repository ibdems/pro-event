from uuid import UUID

from celery import chord, group
from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django_filters.views import FilterView

from .filter import EventFilter
from .forms import ContactForm, EventForms, PayementForm
from .models import Contact, Event, Ticket
from .tasks import generate_and_save_ticket_pdf, send_ticket_by_email


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

                    # Récupération des quantités
                    quantity_normal = int(data.get("quantity_normal", 0))
                    quantity_vip = int(data.get("quantity_vip", 0))
                    quantity_vvip = int(data.get("quantity_vvip", 0))

                    # Création du paiement
                    payement = form.save(commit=False)
                    payement.event = event
                    payement.amount = (
                        (quantity_normal * event.prix_normal)
                        + (quantity_vip * event.prix_vip)
                        + (quantity_vvip * event.prix_vvip)
                    )
                    payement.quantity = quantity_normal + quantity_vip + quantity_vvip
                    payement.save()

                    tasks = []
                    ticket_types = [
                        ("normal", quantity_normal),
                        ("vip", quantity_vip),
                        ("vvip", quantity_vvip),
                    ]

                    # Création des tickets
                    for ticket_type, quantity in ticket_types:
                        for _ in range(quantity):
                            ticket = Ticket.objects.create(
                                payement=payement, event=event, type_ticket=ticket_type
                            )
                            tasks.append(
                                generate_and_save_ticket_pdf.s(event.id, ticket.id, payement.id)
                            )

                    def send_email_after_commit():
                        print(f"No payement envoyer {payement.id} et type: {type(payement.id)}")
                        callback = send_ticket_by_email.si(payement.id)
                        chord(group(tasks))(callback)

                    transaction.on_commit(send_email_after_commit)

                    messages.success(
                        request,
                        "Votre paiement a été effectué avec succès.\n"
                        "Vous recevrez le/les ticket(s) dans l'option de réception choisie.",
                    )
                    return redirect("event:event_detail", uid=event.uid)

            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")
                return self.render_to_response(self.get_context_data(form=form))

        messages.error(request, "Une erreur s'est produite lors du paiement.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class ScanCodeView(View):
    def get(self, request, event_id):
        """
        Affichage de l'événement pour le scan.
        """
        event = get_object_or_404(Event, uid=event_id)
        context = {
            "event": event,
            "total_capacity": event.total_capacity(),
            "tickets_scanned": event.ticket_event.filter(scan_count__gt=0).count(),
            "available_capacity": event.available_capacity(),
        }
        return render(request, "event/scan_ticket.html", context)

    def post(self, request, event_id):
        """
        Vérification du ticket lors du scan.
        """
        code_ticket = request.POST.get("code_ticket")
        print(f"Code ticket {code_ticket}")
        try:
            ticket = Ticket.objects.get(code_ticket=code_ticket)
            print(f"ticket: {ticket}")

            # Vérifier si le ticket correspond à l'événement
            event_id = UUID(event_id)
            print(f"type(event_id): {type(event_id)}, value: {event_id}")
            print(f"type(ticket.event.uid): {type(ticket.event.uid)}, value: {ticket.event.uid}")
            if ticket.event.uid != event_id:
                return JsonResponse(
                    {"success": False, "message": "Ce ticket n'est pas valide pour cet événement."}
                )

            # Vérifier si l'événement est toujours actif
            if not ticket.event.statut:
                return JsonResponse(
                    {"success": False, "message": "Cet événement n'est plus actif."}
                )

            # Vérifier si l'événement n'est pas terminé
            if ticket.event.end_date < timezone.now():
                return JsonResponse({"success": False, "message": "Cet événement est terminé."})

            # Incrémenter le compteur de scan
            ticket.scan_count += 1
            ticket.save()

            message = "Ticket valide."
            if ticket.scan_count > 1:
                message = f"Attention: Ticket déjà scanné {ticket.scan_count} fois."

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "type_ticket": ticket.type_ticket,
                    "scan_count": ticket.scan_count,
                }
            )

        except Ticket.DoesNotExist:
            return JsonResponse({"success": False, "message": "Ticket invalide ou inexistant."})
        except Exception:
            return JsonResponse(
                {"success": False, "message": "Une erreur est survenue lors de la vérification."}
            )
