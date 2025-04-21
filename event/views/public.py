from django.db.models import Prefetch
from django.views.generic import ListView, TemplateView

from event.models import Event, InfoTicket, Partner, Ticket


class HomeView(ListView):
    model = Event
    template_name = "event/accueil.html"
    context_object_name = "events"

    def get_queryset(self):
        qr = super().get_queryset()
        return (
            qr.filter(statut=True, image__isnull=False)
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
            .order_by("-created_at")[:3]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "home"

        context["event_count"] = Event.objects.filter(statut=True).count()

        context["partner_count"] = Partner.objects.count()

        context["ticket_count"] = Ticket.objects.count()

        context["platform_partners"] = Partner.objects.filter(is_platform_partner=True)

        return context


class MentionsLegalesView(TemplateView):
    template_name = "legal/mentions_legales.html"


class ConditionsUtilisationView(TemplateView):
    template_name = "legal/conditions_utilisation.html"


class PolitiqueConfidentialiteView(TemplateView):
    template_name = "legal/politique_confidentialite.html"
